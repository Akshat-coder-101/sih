import random
import string
import asyncio
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from . import models, schemas, security, ledger, seed, video_stream, rule_engine
from .database import Base, engine, get_db
from .ws_manager import manager

Base.metadata.create_all(bind=engine)

app = FastAPI(title="IBVAP Backend", version="0.1.0")

# Demo-friendly CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    db = next(get_db())
    seed.run_seed(db)
    # Start background rule engine for simulated detections, ANPR, Watchlist
    asyncio.create_task(rule_engine.trigger_periodic_rule_events())


def write_audit(db: Session, username: str, action: str, detail: str = None):
    db.add(models.AuditLog(username=username, action=action, detail=detail))
    db.commit()


def alert_to_out(a: models.Alert) -> schemas.AlertOut:
    return schemas.AlertOut(
        id=a.id, type=a.type, sev=a.sev, cam_id=a.cam_id, cam_name=a.cam_name,
        location=a.location, confidence=a.confidence, track_id=a.track_id,
        detail=security.decrypt_field(a.detail_enc), reviewed=a.reviewed, ts=a.ts,
        snapshot=security.decrypt_field(a.snapshot_enc),
    )


def camera_to_out(c: models.Camera) -> schemas.CameraOut:
    if isinstance(c.anchor, dict):
        anchor = schemas.Anchor.model_validate(c.anchor)
    elif isinstance(c.anchor, str):
        anchor = schemas.Anchor.model_validate_json(c.anchor)
    elif isinstance(c.anchor, schemas.Anchor):
        anchor = c.anchor
    else:
        anchor = schemas.Anchor(left=44, top=46, w=9, h=26)

    return schemas.CameraOut(
        id=c.id, name=c.name, location=c.location, online=c.online,
        priority=c.priority, fps=c.fps, night=c.night, scene=c.scene, geo=c.geo,
        anchor=anchor, rtsp_url=c.rtsp_url,
    )


# ---------------------------------------------------------------------------
# Auth (FR-9.2 / FR-9.5)
# ---------------------------------------------------------------------------
@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == body.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    security.check_lockout(user)

    if not security.verify_password(body.password, user.hashed_password):
        security.register_failed_attempt(user, db)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    security.reset_failed_attempts(user, db)
    write_audit(db, user.username, "login")
    token = security.create_access_token(user.username, user.role)
    return schemas.TokenResponse(access_token=token, role=user.role, username=user.username)


@app.get("/auth/me")
def get_me(user: models.User = Depends(security.get_current_user)):
    return {"username": user.username, "role": user.role}


# ---------------------------------------------------------------------------
# Cameras (FR-8.4, FR-1.1 Video Streaming)
# ---------------------------------------------------------------------------
@app.get("/cameras", response_model=list[schemas.CameraOut])
def list_cameras(db: Session = Depends(get_db),
                 user: models.User = Depends(security.require_role("operator", allow_guest_operator=True))):
    return [camera_to_out(c) for c in db.query(models.Camera).all()]


@app.get("/cameras/{cam_id}/stream")
def camera_stream(cam_id: str):
    """Live MJPEG video stream for CAM-02, CAM-03, CAM-04 (FR-1 / FR-8.1)."""
    return StreamingResponse(
        video_stream.stream_mjpeg(cam_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.patch("/cameras/{cam_id}/toggle", response_model=schemas.CameraOut)
def toggle_camera(cam_id: str, db: Session = Depends(get_db),
                  user: models.User = Depends(security.require_role("admin"))):
    cam = db.query(models.Camera).filter(models.Camera.id == cam_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    cam.online = not cam.online
    db.commit()
    db.refresh(cam)
    write_audit(db, user.username, "toggle_camera", detail=f"{cam_id} -> online={cam.online}")
    return camera_to_out(cam)


@app.patch("/cameras/{cam_id}/night", response_model=schemas.CameraOut)
def toggle_night(cam_id: str, db: Session = Depends(get_db),
                 user: models.User = Depends(security.require_role("operator", allow_guest_operator=True))):
    cam = db.query(models.Camera).filter(models.Camera.id == cam_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    cam.night = not cam.night
    db.commit()
    db.refresh(cam)
    if cam_id in video_stream.generators:
        video_stream.generators[cam_id].is_night = cam.night
    write_audit(db, user.username, "toggle_night", detail=f"{cam_id} -> night={cam.night}")
    return camera_to_out(cam)


# ---------------------------------------------------------------------------
# Alerts (FR-5)
# ---------------------------------------------------------------------------
TYPE_DEFAULT_SEV = {
    "intrusion": "high", "watchlist": "high", "anpr": "med",
    "loiter": "med", "night": "low", "weapon": "high",
}


def _next_alert_id(db: Session) -> str:
    count = db.query(models.Alert).count()
    return f"EVT-{count + 1:04d}"


def _rand_track_id() -> str:
    return "#" + str(random.randint(100, 999))


@app.get("/alerts", response_model=list[schemas.AlertOut])
def list_alerts(
    type: str | None = None,
    sev: str | None = None,
    cam_id: str | None = Query(default=None, alias="camId"),
    reviewed: bool | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.require_role("operator", allow_guest_operator=True)),
):
    q = db.query(models.Alert)
    if type:
        q = q.filter(models.Alert.type == type)
    if sev:
        q = q.filter(models.Alert.sev == sev)
    if cam_id:
        q = q.filter(models.Alert.cam_id == cam_id)
    if reviewed is not None:
        q = q.filter(models.Alert.reviewed == reviewed)
    alerts = q.order_by(models.Alert.ts.desc()).all()
    return [alert_to_out(a) for a in alerts]


@app.post("/alerts", response_model=schemas.AlertOut)
async def create_alert(
    body: schemas.AlertCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.require_role("operator", allow_guest_operator=True)),
):
    """Called by AI inference (or client-side webcam detection) whenever an event occurs.
    Persists to SQLite, writes AES-256 encrypted fields, appends to hash-chain ledger,
    and broadcasts over WebSocket."""
    cam = db.query(models.Camera).filter(models.Camera.id == body.cam_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Unknown camera id")

    sev = body.sev or TYPE_DEFAULT_SEV.get(body.type, "med")
    alert = models.Alert(
        id=_next_alert_id(db),
        type=body.type,
        sev=sev,
        cam_id=cam.id,
        cam_name=cam.name,
        location=cam.location,
        confidence=body.confidence if body.confidence is not None else random.randint(78, 98),
        track_id=body.track_id or _rand_track_id(),
        detail_enc=security.encrypt_field(body.detail),
        reviewed=False,
        ts=datetime.utcnow(),
        snapshot_enc=security.encrypt_field(body.snapshot),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    ledger.append_to_ledger(db, alert)

    out = alert_to_out(alert)
    await manager.broadcast_alert(out.model_dump(by_alias=True))
    return out


@app.patch("/alerts/{alert_id}/reviewed", response_model=schemas.AlertOut)
def mark_reviewed(alert_id: str, db: Session = Depends(get_db),
                   user: models.User = Depends(security.require_role("supervisor"))):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.reviewed = True
    db.commit()
    db.refresh(alert)
    write_audit(db, user.username, "mark_reviewed", detail=alert_id)
    return alert_to_out(alert)


# ---------------------------------------------------------------------------
# Ledger (FR-10 / FR-8.6)
# ---------------------------------------------------------------------------
@app.get("/ledger/verify", response_model=schemas.LedgerVerifyResult)
def verify_ledger(db: Session = Depends(get_db),
                   user: models.User = Depends(security.require_role("operator", allow_guest_operator=True))):
    return ledger.verify_chain(db)


@app.post("/ledger/tamper-demo/{alert_id}")
def tamper_demo(alert_id: str, db: Session = Depends(get_db),
                 user: models.User = Depends(security.require_role("admin"))):
    """DEMO-ONLY endpoint: directly mutates an alert's stored detail,
    bypassing the ledger entirely, so you can click 'Verify Log Integrity'
    before and after this call and show it flip from intact -> broken live
    for judges."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    tamper_suffix = "".join(random.choices(string.ascii_uppercase, k=4))
    current = security.decrypt_field(alert.detail_enc)
    alert.detail_enc = security.encrypt_field(current + f" [TAMPERED-{tamper_suffix}]")
    db.commit()
    write_audit(db, user.username, "TAMPER_DEMO", detail=f"Directly edited {alert_id} bypassing ledger")
    return {"status": "tampered", "alert_id": alert_id}


# ---------------------------------------------------------------------------
# Audit log & C2 Integration (FR-9.4 / Phase 5)
# ---------------------------------------------------------------------------
@app.get("/audit-log", response_model=list[schemas.AuditLogOut])
def get_audit_log(db: Session = Depends(get_db),
                   user: models.User = Depends(security.require_role("supervisor"))):
    rows = db.query(models.AuditLog).order_by(models.AuditLog.ts.desc()).limit(200).all()
    return rows


@app.post("/api/c2/mock-webhook")
def c2_mock_webhook(payload: dict):
    """C2 integration relay mock receiver."""
    return {"status": "received", "timestamp": datetime.utcnow().isoformat()}


# ---------------------------------------------------------------------------
# WebSocket push (FR-5.2)
# ---------------------------------------------------------------------------
@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket, token: str = Query(default=None)):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/health")
def health():
    return {"status": "ok", "service": "IBVAP Backend"}
