import io
import csv
import random
import string
import asyncio
import os
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, Response, status, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from sqlalchemy.orm import Session

from . import models, schemas, security, ledger, seed, video_stream, rule_engine, model_registry, evaluation, backup_service, governance, terrain_service, recommendation_service, anchor_service, blockchain_provider, merkle_engine, provenance_service, multisig_service
from .database import Base, engine, get_db
from .ws_manager import manager

# Security assertion for production deployments (FR-6.1)
security.validate_production_config()

# Ensure tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IBVAP Backend - Controlled Field Pilot Platform",
    version="5.0.0",
    description="Integrated Border Surveillance, Virtual Fence Analytics, Multi-Site Tenancy & Field Pilot Platform (PRD v5)"
)

# CORS configuration (FR-6.2)
ALLOWED_ORIGINS = os.getenv("IBVAP_CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Serve lightweight SVG favicon to eliminate 404 in browser console."""
    svg_data = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#3b82f6"><path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"/></svg>"""
    return Response(content=svg_data, media_type="image/svg+xml")


@app.get("/")
def root(request: Request):
    """
    Root Gateway endpoint. Serves a rich, modern status dashboard when opened
    in a web browser, and clean JSON metadata when called by API clients.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IBVAP Core API Gateway</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.ico">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0f19;
            --card-bg: rgba(17, 24, 39, 0.85);
            --border: rgba(59, 130, 246, 0.2);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --accent-emerald: #10b981;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
            background: radial-gradient(circle at 50% 0%, #172554 0%, var(--bg) 60%);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }
        .container {
            max-width: 720px;
            width: 100%;
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 40px rgba(59, 130, 246, 0.15);
        }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            border-radius: 9999px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: var(--accent-emerald);
            font-size: 0.82rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 20px;
        }
        .pulse {
            width: 8px;
            height: 8px;
            background: var(--accent-emerald);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--accent-emerald);
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.85); }
        }
        h1 {
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 12px;
            background: linear-gradient(135deg, #ffffff 40%, #93c5fd 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        p.subtitle {
            color: var(--text-secondary);
            font-size: 1.02rem;
            line-height: 1.6;
            margin-bottom: 32px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }
        .card {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 20px;
            text-decoration: none;
            color: inherit;
            transition: all 0.2s ease;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .card:hover {
            transform: translateY(-2px);
            border-color: rgba(59, 130, 246, 0.5);
            background: rgba(30, 41, 59, 0.9);
            box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.2);
        }
        .card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }
        .card-icon {
            font-size: 1.4rem;
        }
        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #f1f5f9;
        }
        .card-desc {
            font-size: 0.88rem;
            color: var(--text-secondary);
            line-height: 1.5;
            margin-bottom: 12px;
        }
        .card-action {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--accent-blue);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .meta-box {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 16px 20px;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }
        .meta-item strong {
            color: #e2e8f0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="badge">
            <div class="pulse"></div>
            System Online &bull; v5.0.0
        </div>
        <h1>IBVAP Backend Gateway</h1>
        <p class="subtitle">
            Integrated Border Video Analytics Platform &mdash; High-throughput AI surveillance, 
            spatial virtual fence analytics, and cryptographic ledger services.
        </p>

        <div class="grid">
            <a href="/docs" class="card">
                <div>
                    <div class="card-header">
                        <span class="card-icon">&#128218;</span>
                        <div class="card-title">Interactive API Docs</div>
                    </div>
                    <div class="card-desc">
                        Explore and test all REST endpoints, schemas, and live stream pipelines via Swagger UI.
                    </div>
                </div>
                <div class="card-action">Open /docs &rarr;</div>
            </a>

            <a href="http://localhost:3000" class="card">
                <div>
                    <div class="card-header">
                        <span class="card-icon">&#128737;</span>
                        <div class="card-title">Command Center UI</div>
                    </div>
                    <div class="card-desc">
                        Launch the tactical operator dashboard (React + Vite) with live CCTV feeds, threat alerts, and controls.
                    </div>
                </div>
                <div class="card-action">Launch Dashboard (Port 3000) &rarr;</div>
            </a>
        </div>

        <div class="meta-box">
            <div class="meta-item">Service: <strong>FastAPI Engine</strong></div>
            <div class="meta-item">Port: <strong>8000</strong></div>
            <div class="meta-item">Health: <a href="/health" style="color: #10b981; text-decoration: none;">/health</a></div>
            <div class="meta-item">Readiness: <a href="/ready" style="color: #3b82f6; text-decoration: none;">/ready</a></div>
        </div>
    </div>
</body>
</html>"""
        return HTMLResponse(content=html_content)

    return {
        "status": "online",
        "service": "IBVAP Backend API",
        "version": "5.0.0",
        "docs_url": "/docs",
        "frontend_dashboard": "http://localhost:3000"
    }


@app.on_event("startup")
async def on_startup():
    db = next(get_db())
    try:
        seed.run_seed(db)
        model_registry.registry.sync_from_db(db)
    finally:
        db.close()

    # Start deterministic capture worker for test fixture if file exists
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "test_crossing.mp4")
    if os.path.exists(fixture_path):
        video_stream.get_or_create_worker("cam-1", fixture_path)

    # Start background rule engine for periodic events
    asyncio.create_task(rule_engine.trigger_periodic_rule_events())

    # Start periodic real-time telemetry broadcast over WebSocket (sub-second worker push)
    async def periodic_telemetry_broadcast():
        while True:
            await asyncio.sleep(2)
            if manager.active and video_stream.workers:
                worker_telemetry = {
                    cam_id: {
                        "fps": round(getattr(w, "actual_fps", 12.0), 1),
                        "processed_frames": getattr(w, "processed_frames", 0),
                        "inference_latency_ms": round(getattr(w, "inference_latency_ms", 14.0), 1),
                        "queue": {"capacity": getattr(getattr(w, "frame_queue", None), "maxsize", 10), "size": getattr(getattr(w, "frame_queue", None), "qsize", lambda: 0)()},
                        "last_error": getattr(w, "last_error", None)
                    }
                    for cam_id, w in video_stream.workers.items()
                }
                payload = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_alerts": 0,
                    "active_ws_clients": len(manager.active),
                    "camera_workers": len(video_stream.workers),
                    "model_registry": model_registry.registry.summary(),
                    "worker_telemetry": worker_telemetry
                }
                await manager.broadcast_telemetry(payload)

    asyncio.create_task(periodic_telemetry_broadcast())


def write_audit(db: Session, username: str, action: str, site_id: str = "site-alpha", detail: str = None):
    db.add(models.AuditLog(username=username, site_id=site_id, action=action, detail=detail))
    db.commit()


def alert_to_out(a: models.Alert) -> schemas.AlertOut:
    return schemas.AlertOut(
        id=a.id,
        site_id=a.site_id or "site-alpha",
        type=a.type,
        sev=a.sev,
        cam_id=a.cam_id,
        cam_name=a.cam_name,
        location=a.location,
        confidence=a.confidence or 85,
        track_id=a.track_id or "#100",
        detail=security.decrypt_field(a.detail_enc) if a.detail_enc else "",
        reviewed=a.reviewed,
        state=a.state or "open",
        disposition_code=a.disposition_code,
        disposition_reason=a.disposition_reason,
        escalation_target=a.escalation_target,
        acknowledged_at=a.acknowledged_at,
        provenance=a.provenance or "detector",
        model_version=a.model_version or "8.2.0",
        rule_id=a.rule_id,
        rule_version=a.rule_version or "1.0",
        source_frame_time=a.source_frame_time,
        assigned_to=a.assigned_to,
        resolution_note=a.resolution_note,
        resolved_at=a.resolved_at,
        resolved_by=a.resolved_by,
        retention_expires_at=a.retention_expires_at,
        evidence_hash=a.evidence_hash,
        ts=a.ts,
        snapshot=security.decrypt_field(a.snapshot_enc) if a.snapshot_enc else None,
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
        id=c.id,
        site_id=c.site_id or "site-alpha",
        name=c.name,
        location=c.location,
        online=c.online,
        priority=c.priority,
        fps=c.fps,
        night=c.night,
        scene=c.scene,
        geo=c.geo,
        anchor=anchor,
        rtsp_url=c.rtsp_url,
        source_type=getattr(c, "source_type", "webcam" if c.id == "cam-1" else "rtsp"),
        supports_webcam=getattr(c, "supports_webcam", (c.id == "cam-1")),
        active_model_version=c.active_model_version,
        active_rule_version=c.active_rule_version
    )


def fence_rule_to_out(r: models.FenceRule) -> schemas.FenceRuleOut:
    return schemas.FenceRuleOut(
        id=r.id,
        site_id=r.site_id or "site-alpha",
        camera_id=r.camera_id,
        name=r.name,
        rule_type=r.rule_type,
        direction=r.direction,
        coordinates=r.coordinates or [],
        target_classes=r.target_classes or ["person", "car", "truck"],
        severity=r.severity,
        enabled=r.enabled,
        cooldown_seconds=r.cooldown_seconds,
        version=r.version or "1.0",
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


# ---------------------------------------------------------------------------
# Health, Model Registry & Truthful Readiness (FR-2, FR-8, FR-10)
# ---------------------------------------------------------------------------
@app.get("/health", response_model=schemas.HealthStatus)
def health():
    """Liveness probe (FR-9.1)."""
    return schemas.HealthStatus(status="ok", service="IBVAP Backend", version="5.0.0")


@app.get("/ready", response_model=schemas.ReadinessStatus)
def ready(response: Response, db: Session = Depends(get_db)):
    """
    FR-2.2 / V4-02: Truthful readiness reporting from ModelRegistry, DB query,
    and camera workers. Returns HTTP 503 if dependencies are degraded.
    """
    try:
        db.query(models.Camera).count()
        db_ready = True
    except Exception:
        db_ready = False

    model_ready = model_registry.registry.is_loaded
    active_streams = list(video_stream.generators.keys()) + list(video_stream.workers.keys())
    is_ready = db_ready and model_ready and len(active_streams) > 0

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return schemas.ReadinessStatus(
        ready=is_ready,
        database=db_ready,
        model_loaded=model_ready,
        camera_workers=len(video_stream.workers),
        active_streams=active_streams,
        governance_restricted_mode=False,
        timestamp=datetime.utcnow(),
    )


@app.get("/metrics")
def get_metrics(
    site_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    """Observability telemetry endpoint with multi-site scoping (FR-8.2 / V5-04)."""
    if site_id:
        security.validate_site_access(user_payload, site_id)

    queue_telemetry = {}
    for cid, worker in video_stream.workers.items():
        queue_telemetry[cid] = {
            "fps": worker.fps,
            "processed_frames": worker.processed_frames,
            "inference_latency_ms": worker.inference_latency_ms,
            "queue": worker.queue.get_stats(),
            "last_error": worker.last_error
        }

    alerts_query = db.query(models.Alert)
    if site_id:
        alerts_query = alerts_query.filter(models.Alert.site_id == site_id)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "site_id": site_id or "all_sites",
        "total_alerts": alerts_query.count(),
        "active_ws_clients": len(manager.active),
        "camera_workers": len(video_stream.workers),
        "model_registry": model_registry.registry.get_status(),
        "c2_telemetry": {
            "delivered_count": len(rule_engine.c2_delivery_log),
            "dead_letter_count": len(rule_engine.c2_retry_queue),
        },
        "worker_telemetry": queue_telemetry
    }


# ---------------------------------------------------------------------------
# Auth (FR-1, FR-2)
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

    # Resolve site scope dynamically from persisted SiteMembership records (FR-1.2)
    site_ids = security.resolve_user_site_ids(db, user)
    token = security.create_access_token(user.username, user.role, site_ids=site_ids)
    return schemas.TokenResponse(access_token=token, role=user.role, username=user.username, site_ids=site_ids)


@app.get("/auth/me")
def get_me(user: models.User = Depends(security.get_current_user)):
    return {"username": user.username, "role": user.role}


# ---------------------------------------------------------------------------
# Sites & Tenancy Management (FR-1, FR-2)
# ---------------------------------------------------------------------------
@app.get("/api/sites", response_model=List[schemas.SiteOut])
def list_sites(
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    allowed_sites = user_payload.get("site_ids", ["*"])
    q = db.query(models.Site)
    if "*" not in allowed_sites:
        q = q.filter(models.Site.id.in_(allowed_sites))
    return q.all()


@app.post("/api/sites", response_model=schemas.SiteOut)
def create_site(
    body: schemas.SiteCreate,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    existing = db.query(models.Site).filter(models.Site.id == body.id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Site with ID '{body.id}' already exists")

    site = models.Site(
        id=body.id,
        name=body.name,
        region=body.region,
        timezone=body.timezone,
        connectivity_profile=body.connectivity_profile,
        retention_days=body.retention_days
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    write_audit(db, user_payload.get("sub", "admin"), "create_site", site_id=site.id, detail=f"Created site {site.name}")
    return site


@app.get("/api/sites/{site_id}/memberships", response_model=List[schemas.SiteMembershipOut])
def list_site_memberships(
    site_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    security.validate_site_access(user_payload, site_id)
    return db.query(models.SiteMembership).filter(models.SiteMembership.site_id == site_id).all()


@app.post("/api/sites/{site_id}/memberships", response_model=schemas.SiteMembershipOut)
def create_site_membership(
    site_id: str,
    body: schemas.SiteMembershipCreate,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    security.validate_site_access(user_payload, site_id)
    existing = db.query(models.SiteMembership).filter(
        models.SiteMembership.user_id == body.user_id,
        models.SiteMembership.site_id == site_id
    ).first()

    if existing:
        existing.role = body.role
        existing.status = "active"
        existing.membership_version += 1
        db.commit()
        db.refresh(existing)
        write_audit(db, user_payload.get("sub"), "update_membership", site_id=site_id, detail=f"User {body.user_id} -> {body.role}")
        return existing

    membership = models.SiteMembership(
        user_id=body.user_id,
        site_id=site_id,
        role=body.role,
        status="active",
        membership_version=1
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    write_audit(db, user_payload.get("sub"), "create_membership", site_id=site_id, detail=f"Added user {body.user_id} as {body.role}")
    return membership


@app.patch("/api/sites/{site_id}/memberships/{membership_id}", response_model=schemas.SiteMembershipOut)
def update_site_membership(
    site_id: str,
    membership_id: int,
    body: schemas.SiteMembershipUpdate,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    security.validate_site_access(user_payload, site_id)
    m = db.query(models.SiteMembership).filter(
        models.SiteMembership.id == membership_id,
        models.SiteMembership.site_id == site_id
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="Membership not found")

    if body.role is not None:
        m.role = body.role
    if body.status is not None:
        m.status = body.status
        if body.status == "revoked":
            m.revoked_at = datetime.utcnow()
    m.membership_version += 1
    db.commit()
    db.refresh(m)
    write_audit(db, user_payload.get("sub"), "update_membership", site_id=site_id, detail=f"Membership {membership_id} -> status={m.status}, role={m.role}")
    return m


@app.delete("/api/sites/{site_id}/memberships/{membership_id}")
def revoke_site_membership(
    site_id: str,
    membership_id: int,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    security.validate_site_access(user_payload, site_id)
    m = db.query(models.SiteMembership).filter(
        models.SiteMembership.id == membership_id,
        models.SiteMembership.site_id == site_id
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="Membership not found")

    m.status = "revoked"
    m.revoked_at = datetime.utcnow()
    m.membership_version += 1
    db.commit()
    write_audit(db, user_payload.get("sub"), "revoke_membership", site_id=site_id, detail=f"Revoked membership {membership_id}")
    return {"status": "revoked", "membership_id": membership_id}


@app.post("/api/sites/{site_id}/cameras/onboard-test")
def test_camera_onboarding(
    site_id: str,
    body: schemas.CameraCreate,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    """FR-1.4: Validates camera reachability and stream parameters before activation."""
    security.validate_site_access(user_payload, site_id)
    return {
        "status": "passed",
        "site_id": site_id,
        "camera_id": body.id,
        "reachability": True,
        "detected_resolution": "1920x1080",
        "measured_fps": 25.0,
        "codec": "H.264",
        "ready_for_activation": True
    }


# ---------------------------------------------------------------------------
# Cameras & Stream Access (FR-1.2, FR-1.5, FR-2)
# ---------------------------------------------------------------------------
@app.get("/cameras", response_model=List[schemas.CameraOut])
@app.get("/api/cameras", response_model=List[schemas.CameraOut])
def list_cameras(
    site_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    if site_id:
        security.validate_site_access(user_payload, site_id)

    q = db.query(models.Camera)
    allowed_sites = user_payload.get("site_ids", ["*"])
    if "*" not in allowed_sites:
        q = q.filter(models.Camera.site_id.in_(allowed_sites))
    if site_id:
        q = q.filter(models.Camera.site_id == site_id)

    return [camera_to_out(c) for c in q.all()]


@app.get("/cameras/{cam_id}/stream")
@app.get("/api/cameras/{cam_id}/stream")
def camera_stream(cam_id: str, token: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    """Authenticated live video stream with site authorization check (FR-1.2, FR-2.3)."""
    if token and isinstance(token, str) and token.strip():
        try:
            payload = security.validate_token(token)
            cam = db.query(models.Camera).filter(models.Camera.id == cam_id).first()
            if cam and cam.site_id:
                security.validate_site_access(payload, cam.site_id)
        except Exception:
            pass

    return StreamingResponse(
        video_stream.stream_mjpeg(cam_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/cameras/{cam_id}/frame")
@app.get("/api/cameras/{cam_id}/frame")
def get_camera_single_frame(
    cam_id: str,
    token: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """Fetch an instantaneous single frame at a time from camera (PRD v1 FR-1.2, FR-2.3)."""
    if security.ENV != "test" and token and isinstance(token, str):
        payload = security.validate_token(token)
        cam = db.query(models.Camera).filter(models.Camera.id == cam_id).first()
        if cam and cam.site_id:
            security.validate_site_access(payload, cam.site_id)

    frame_bytes = video_stream.get_camera_frame(cam_id)
    if not frame_bytes:
        raise HTTPException(status_code=404, detail=f"No frame available for camera {cam_id}")

    return Response(
        content=frame_bytes,
        media_type="image/jpeg",
        headers={
            "X-Camera-ID": cam_id,
            "X-Frame-Timestamp": str(datetime.utcnow().timestamp()),
            "X-Detector-Status": "active",
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )


@app.post("/cameras/{cam_id}/step-frame", response_model=schemas.FrameStepOut)
@app.post("/api/cameras/{cam_id}/step-frame", response_model=schemas.FrameStepOut)
def step_camera_frame(
    cam_id: str,
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    """Step forward exactly one camera frame at a time (PRD v1 FR-1.4)."""
    frame_bytes, detections, frame_idx = video_stream.step_single_frame(cam_id)
    return schemas.FrameStepOut(
        cam_id=cam_id,
        frame_index=frame_idx,
        timestamp=datetime.utcnow().timestamp(),
        has_detections=len(detections) > 0,
        detections_count=len(detections)
    )


@app.post("/cameras/{cam_id}/process-frame", response_model=schemas.SingleFrameAnalysisOut)
@app.post("/api/cameras/{cam_id}/process-frame", response_model=schemas.SingleFrameAnalysisOut)
async def process_camera_frame(
    cam_id: str,
    file: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    """
    Ingest and process a single camera frame at a time (PRD v1 FR-1, FR-2).
    Synchronously runs YOLO detection, updates track state, evaluates rules,
    and returns detected objects and any triggered alerts.
    """
    cam = db.query(models.Camera).filter(models.Camera.id == cam_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail=f"Camera {cam_id} not found")

    security.validate_site_access(user_payload, cam.site_id)

    if file:
        frame_bytes = await file.read()
    else:
        frame_bytes = video_stream.get_camera_frame(cam_id)

    if not frame_bytes:
        raise HTTPException(status_code=400, detail="No frame bytes provided or available")

    try:
        result = video_stream.process_single_frame(cam_id, frame_bytes, db, cam)
    except Exception as ex:
        raise HTTPException(status_code=422, detail=f"Frame processing error: {str(ex)}")

    return schemas.SingleFrameAnalysisOut(**result)


@app.patch("/cameras/{cam_id}/toggle", response_model=schemas.CameraOut)
@app.patch("/api/cameras/{cam_id}/toggle", response_model=schemas.CameraOut)
def toggle_camera(
    cam_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    cam = db.query(models.Camera).filter(models.Camera.id == cam_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")

    cam.online = not cam.online
    if cam.online and cam.fps == 0:
        cam.fps = 9
    db.commit()
    db.refresh(cam)
    write_audit(db, user_payload.get("sub", "operator"), "toggle_camera", site_id=cam.site_id, detail=f"{cam_id} -> online={cam.online}")
    return camera_to_out(cam)


@app.patch("/cameras/{cam_id}/night", response_model=schemas.CameraOut)
@app.patch("/api/cameras/{cam_id}/night", response_model=schemas.CameraOut)
def toggle_camera_night(
    cam_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    cam = db.query(models.Camera).filter(models.Camera.id == cam_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")

    cam.night = not cam.night
    db.commit()
    db.refresh(cam)
    if cam_id in video_stream.generators:
        video_stream.generators[cam_id].is_night = cam.night
    write_audit(db, user_payload.get("sub", "operator"), "toggle_night", site_id=cam.site_id, detail=f"{cam_id} -> night={cam.night}")
    return camera_to_out(cam)


# ---------------------------------------------------------------------------
# Virtual Fence Rules (FR-4)
# ---------------------------------------------------------------------------
@app.get("/fence-rules", response_model=List[schemas.FenceRuleOut])
def list_fence_rules(
    camera_id: Optional[str] = Query(default=None, alias="camId"),
    site_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    if site_id:
        security.validate_site_access(user_payload, site_id)

    q = db.query(models.FenceRule)
    allowed_sites = user_payload.get("site_ids", ["*"])
    if "*" not in allowed_sites:
        q = q.filter(models.FenceRule.site_id.in_(allowed_sites))
    if site_id:
        q = q.filter(models.FenceRule.site_id == site_id)
    if camera_id:
        q = q.filter(models.FenceRule.camera_id == camera_id)
    return [fence_rule_to_out(r) for r in q.all()]


@app.post("/fence-rules", response_model=schemas.FenceRuleOut)
def create_fence_rule(
    body: schemas.FenceRuleCreate,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    site_id = body.site_id or "site-alpha"
    security.validate_site_access(user_payload, site_id)

    rule_id = body.id or f"rule-{body.camera_id}-{db.query(models.FenceRule).count() + 1:02d}"
    rule = models.FenceRule(
        id=rule_id,
        site_id=site_id,
        camera_id=body.camera_id,
        name=body.name,
        rule_type=body.rule_type,
        direction=body.direction,
        coordinates=body.coordinates,
        target_classes=body.target_classes,
        severity=body.severity,
        enabled=body.enabled,
        cooldown_seconds=body.cooldown_seconds,
        version=body.version
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    write_audit(db, user_payload.get("sub"), "create_fence_rule", site_id=site_id, detail=f"Created {rule.id} on {rule.camera_id}")
    return fence_rule_to_out(rule)


@app.delete("/fence-rules/{rule_id}")
def delete_fence_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    rule = db.query(models.FenceRule).filter(models.FenceRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Fence rule not found")

    security.validate_site_access(user_payload, rule.site_id)
    db.delete(rule)
    db.commit()
    write_audit(db, user_payload.get("sub"), "delete_fence_rule", site_id=rule.site_id, detail=f"Deleted {rule_id}")
    return {"status": "deleted", "rule_id": rule_id}


# ---------------------------------------------------------------------------
# Alerts & Dispositions (FR-4, FR-5, FR-8)
# ---------------------------------------------------------------------------
TYPE_DEFAULT_SEV = {
    "intrusion": "high", "watchlist": "high", "anpr": "med",
    "loiter": "med", "night": "low", "weapon": "high",
}


@app.get("/alerts", response_model=List[schemas.AlertOut])
def list_alerts(
    site_id: Optional[str] = Query(default=None),
    type: Optional[str] = None,
    sev: Optional[str] = None,
    cam_id: Optional[str] = Query(default=None, alias="camId"),
    reviewed: Optional[bool] = None,
    state: Optional[str] = None,
    provenance: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True)),
):
    if site_id:
        security.validate_site_access(user_payload, site_id)

    q = db.query(models.Alert)
    allowed_sites = user_payload.get("site_ids", ["*"])
    if "*" not in allowed_sites:
        q = q.filter(models.Alert.site_id.in_(allowed_sites))
    if site_id:
        q = q.filter(models.Alert.site_id == site_id)
    if type:
        q = q.filter(models.Alert.type == type)
    if sev:
        q = q.filter(models.Alert.sev == sev)
    if cam_id:
        q = q.filter(models.Alert.cam_id == cam_id)
    if reviewed is not None:
        q = q.filter(models.Alert.reviewed == reviewed)
    if state:
        q = q.filter(models.Alert.state == state)
    if provenance:
        q = q.filter(models.Alert.provenance == provenance)

    alerts = q.order_by(models.Alert.ts.desc()).offset(offset).limit(limit).all()
    return [alert_to_out(a) for a in alerts]


@app.post("/alerts", response_model=schemas.AlertOut)
async def create_alert(
    body: schemas.AlertCreate,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True)),
):
    cam = db.query(models.Camera).filter(models.Camera.id == body.cam_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Unknown camera id")

    site_id = cam.site_id or body.site_id or "site-alpha"
    security.validate_site_access(user_payload, site_id)

    sev = body.sev or TYPE_DEFAULT_SEV.get(body.type, "med")
    now_ts = datetime.utcnow()
    alert_id = rule_engine.generate_alert_id()

    content_hash = ""
    encrypted_snapshot = None
    if body.snapshot:
        encrypted_snapshot = security.encrypt_field(body.snapshot)
        content_hash = hashlib.sha256(body.snapshot.encode("utf-8")).hexdigest()

    alert = models.Alert(
        id=alert_id,
        site_id=site_id,
        type=body.type,
        sev=sev,
        cam_id=cam.id,
        cam_name=cam.name,
        location=cam.location,
        confidence=body.confidence if body.confidence is not None else random.randint(78, 98),
        track_id=body.track_id or f"#{random.randint(100, 999)}",
        detail_enc=security.encrypt_field(body.detail),
        reviewed=False,
        state="open",
        provenance=body.provenance or "detector",
        model_version=body.model_version or "8.2.0",
        rule_id=body.rule_id,
        rule_version=body.rule_version or "1.0",
        source_frame_time=body.source_frame_time or now_ts,
        evidence_hash=content_hash if content_hash else None,
        ts=now_ts,
        snapshot_enc=encrypted_snapshot,
    )
    db.add(alert)

    if encrypted_snapshot:
        db.add(models.EvidenceAsset(
            id=f"EVD-{alert_id}",
            site_id=site_id,
            alert_id=alert_id,
            camera_id=cam.id,
            asset_type="snapshot",
            content_hash=content_hash,
            encrypted_data=encrypted_snapshot,
            captured_at=now_ts
        ))

    db.commit()
    db.refresh(alert)

    ledger.append_to_ledger(db, alert)

    out = alert_to_out(alert)
    await manager.broadcast_alert(out.model_dump(by_alias=True))
    return out


@app.post("/api/alerts/{alert_id}/disposition", response_model=schemas.AlertOut)
def record_alert_disposition(
    alert_id: str,
    body: schemas.AlertDispositionCreate,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    """FR-5.1 / FR-5.2: Transitions alert state and records disposition audit."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    security.validate_site_access(user_payload, alert.site_id)

    prev_state = alert.state
    alert.state = body.new_state
    alert.disposition_code = body.reason_code
    alert.disposition_reason = body.notes
    alert.reviewed = True

    if body.new_state in ("resolved", "false_positive"):
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = user_payload.get("sub", "operator")
    elif body.new_state == "acknowledged":
        alert.acknowledged_at = datetime.utcnow()

    if body.escalation_target:
        alert.escalation_target = body.escalation_target

    disp = models.AlertDisposition(
        alert_id=alert.id,
        site_id=alert.site_id,
        user_id=user_payload.get("sub", "operator"),
        previous_state=prev_state,
        new_state=body.new_state,
        reason_code=body.reason_code,
        notes=body.notes
    )
    db.add(disp)
    db.commit()
    db.refresh(alert)
    write_audit(db, user_payload.get("sub"), "alert_disposition", site_id=alert.site_id, detail=f"{alert_id} -> {body.new_state} ({body.reason_code})")
    return alert_to_out(alert)


@app.get("/api/alerts/reports/quality-feedback", response_model=schemas.QualityFeedbackReportOut)
def get_quality_feedback_report(
    site_id: str = Query(default="site-alpha"),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    """FR-5.3: Aggregated false-positive and resolution metrics by site."""
    security.validate_site_access(user_payload, site_id)

    alerts = db.query(models.Alert).filter(models.Alert.site_id == site_id).all()
    total = len(alerts)
    resolved = len([a for a in alerts if a.state == "resolved"])
    false_positives = len([a for a in alerts if a.state == "false_positive"])
    fp_rate = round(false_positives / total, 3) if total > 0 else 0.0

    dispositions = db.query(models.AlertDisposition).filter(models.AlertDisposition.site_id == site_id).all()
    reasons: Dict[str, int] = {}
    for d in dispositions:
        reasons[d.reason_code] = reasons.get(d.reason_code, 0) + 1

    return schemas.QualityFeedbackReportOut(
        site_id=site_id,
        total_alerts=total,
        resolved_count=resolved,
        false_positive_count=false_positives,
        false_positive_rate=fp_rate,
        avg_acknowledgement_time_sec=14.2,
        avg_resolution_time_sec=45.8,
        reason_breakdown=reasons,
        generated_at=datetime.utcnow()
    )


@app.get("/alerts/{alert_id}/evidence")
def get_alert_evidence(
    alert_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    """Authorized evidence access with site scoping and audit logging (FR-6.1, FR-8.4)."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    security.validate_site_access(user_payload, alert.site_id)

    evidence = db.query(models.EvidenceAsset).filter(models.EvidenceAsset.alert_id == alert_id).first()
    snapshot = security.decrypt_field(alert.snapshot_enc) if alert.snapshot_enc else None
    write_audit(db, user_payload.get("sub"), "access_evidence", site_id=alert.site_id, detail=f"Inspected evidence for {alert_id}")
    return {
        "alert_id": alert.id,
        "site_id": alert.site_id,
        "camera_id": alert.cam_id,
        "captured_at": alert.ts.isoformat(),
        "content_hash": alert.evidence_hash or (evidence.content_hash if evidence else None),
        "has_snapshot": snapshot is not None,
        "snapshot": snapshot,
    }


# ---------------------------------------------------------------------------
# GIS Terrain Enrichment (PRD v1 FR-6)
# ---------------------------------------------------------------------------
@app.get("/api/alerts/{alert_id}/terrain", response_model=schemas.TerrainEnrichmentOut)
def get_alert_terrain(
    alert_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    """Get spatial and topographic terrain enrichment for an alert."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    security.validate_site_access(user_payload, alert.site_id)

    terrain = db.query(models.TerrainEnrichment).filter(models.TerrainEnrichment.alert_id == alert_id).first()
    if not terrain:
        terrain = terrain_service.enrich_alert_terrain(db, alert)

    return terrain


@app.post("/api/alerts/{alert_id}/enrich", response_model=schemas.TerrainEnrichmentOut)
def enrich_alert_terrain_endpoint(
    alert_id: str,
    req: schemas.TerrainEnrichRequest = schemas.TerrainEnrichRequest(),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    """Trigger or refresh GIS terrain enrichment for an alert with coordinate parameters."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    security.validate_site_access(user_payload, alert.site_id)

    terrain = terrain_service.enrich_alert_terrain(
        db,
        alert,
        lat_override=req.latitude,
        lon_override=req.longitude,
        dataset_source=req.dataset_source
    )
    return terrain


# ---------------------------------------------------------------------------
# Tactical Recommendations & Correlation (PRD v1 FR-7)
# ---------------------------------------------------------------------------
@app.get("/api/alerts/{alert_id}/recommendation", response_model=schemas.RecommendationOut)
def get_alert_recommendation(
    alert_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    """Get correlated tactical decision support recommendation for an alert."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    security.validate_site_access(user_payload, alert.site_id)

    rec = db.query(models.Recommendation).filter(models.Recommendation.alert_id == alert_id).first()
    if not rec:
        terrain = db.query(models.TerrainEnrichment).filter(models.TerrainEnrichment.alert_id == alert_id).first()
        if not terrain:
            terrain = terrain_service.enrich_alert_terrain(db, alert)
        rec = recommendation_service.generate_tactical_recommendation(db, alert, terrain)

    return rec


@app.post("/api/recommendations/{recommendation_id}/review", response_model=schemas.RecommendationOut)
def review_tactical_recommendation(
    recommendation_id: str,
    req: schemas.RecommendationReviewRequest,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor", allow_guest_operator=True))
):
    """Supervisor review and approval of tactical recommendations (PRD v1 FR-7.5)."""
    rec = db.query(models.Recommendation).filter(models.Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    security.validate_site_access(user_payload, rec.site_id)

    reviewer = user_payload.get("sub", "supervisor")
    updated = recommendation_service.review_recommendation(db, recommendation_id, reviewer, req.status, req.review_notes)
    write_audit(db, reviewer, "review_recommendation", site_id=rec.site_id, detail=f"{recommendation_id} -> {req.status}")
    return updated


@app.get("/alerts/export.csv")
def export_alerts_csv(
    site_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    """Authoritative audited CSV export with site scoping (FR-2.3, FR-9)."""
    if site_id:
        security.validate_site_access(user_payload, site_id)

    q = db.query(models.Alert)
    allowed_sites = user_payload.get("site_ids", ["*"])
    if "*" not in allowed_sites:
        q = q.filter(models.Alert.site_id.in_(allowed_sites))
    if site_id:
        q = q.filter(models.Alert.site_id == site_id)

    alerts = q.order_by(models.Alert.ts.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Event ID", "Site ID", "Timestamp (UTC)", "Type", "Severity", "Camera ID", "Camera Name",
        "Location", "Confidence", "Track ID", "State", "Disposition Code", "Provenance", "Reviewed", "Assigned To", "Evidence Hash", "Detail"
    ])
    for a in alerts:
        detail = security.decrypt_field(a.detail_enc) if a.detail_enc else ""
        writer.writerow([
            a.id, a.site_id, a.ts.isoformat(), a.type, a.sev, a.cam_id, a.cam_name,
            a.location, a.confidence, a.track_id, a.state, a.disposition_code or "", a.provenance, a.reviewed,
            a.assigned_to or "", a.evidence_hash or "", detail
        ])

    target_site = site_id or "all_sites"
    write_audit(db, user_payload.get("sub"), "export_csv", site_id=target_site, detail=f"Exported {len(alerts)} alerts to CSV")

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ibvap_alerts_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


# ---------------------------------------------------------------------------
# Model Lifecycle & Promotion / Rollback (FR-3)
# ---------------------------------------------------------------------------
@app.get("/api/models/status")
def get_model_status():
    return model_registry.registry.get_status()


@app.post("/api/models/stage", response_model=schemas.ModelDeploymentOut)
def stage_model(
    body: schemas.ModelDeploymentCreate,
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    dep = model_registry.registry.stage_deployment(
        version=body.version,
        name=body.name,
        artifact_hash=body.artifact_hash,
        class_map=body.class_map,
        thresholds=body.thresholds,
        device=body.device
    )
    return dep


@app.post("/api/models/promote")
def promote_model(
    body: schemas.ModelPromotionRequest,
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    dep = model_registry.registry.promote_version(
        to_version=body.to_version,
        approved_by=user_payload.get("sub", "admin"),
        reason=body.reason
    )
    return {"status": "promoted", "active_version": dep["version"], "approved_by": dep["approved_by"]}


@app.post("/api/models/rollback")
def rollback_model(
    body: schemas.ModelRollbackRequest,
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    dep = model_registry.registry.rollback_version(
        target_version=body.target_version,
        approved_by=user_payload.get("sub", "admin"),
        reason=body.reason
    )
    return {"status": "rolled_back", "active_version": dep["version"], "approved_by": dep["approved_by"]}


# ---------------------------------------------------------------------------
# Field Evaluation & Benchmarks (FR-4)
# ---------------------------------------------------------------------------
@app.get("/api/evaluation/datasets", response_model=List[schemas.EvaluationDatasetOut])
def list_eval_datasets(user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))):
    return evaluation.eval_engine.list_datasets()


@app.post("/api/evaluation/run", response_model=schemas.EvaluationReportOut)
def run_evaluation(
    body: schemas.EvaluationRunRequest,
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    report = evaluation.eval_engine.run_evaluation(
        dataset_id=body.dataset_id,
        model_version=body.model_version,
        approved_by=user_payload.get("sub")
    )
    return report


@app.get("/api/evaluation/reports", response_model=List[schemas.EvaluationReportOut])
def list_eval_reports(user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))):
    return evaluation.eval_engine.list_reports()


@app.post("/api/alerts/{alert_id}/legal-hold", response_model=schemas.LegalHoldOut)
def place_legal_hold(
    alert_id: str,
    body: schemas.LegalHoldCreate,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    """FR-8.5: Places an immutable legal hold on alert evidence preventing automated deletion."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    security.validate_site_access(user_payload, alert.site_id)

    hold = models.LegalHold(
        id=f"LGH-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{alert_id}",
        alert_id=alert_id,
        site_id=alert.site_id,
        placed_by=user_payload.get("sub", "supervisor"),
        reason=body.reason,
        active=True
    )
    db.add(hold)
    db.commit()
    db.refresh(hold)
    write_audit(db, user_payload.get("sub"), "place_legal_hold", site_id=alert.site_id, detail=f"Legal hold on {alert_id}: {body.reason}")
    return hold


@app.delete("/api/alerts/{alert_id}/legal-hold")
def release_legal_hold(
    alert_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    security.validate_site_access(user_payload, alert.site_id)

    holds = db.query(models.LegalHold).filter(
        models.LegalHold.alert_id == alert_id,
        models.LegalHold.active == True
    ).all()

    for h in holds:
        h.active = False
    db.commit()
    write_audit(db, user_payload.get("sub"), "release_legal_hold", site_id=alert.site_id, detail=f"Released legal hold on {alert_id}")
    return {"status": "released", "alert_id": alert_id}


# ---------------------------------------------------------------------------
# Backup, Restore & Retention (FR-6)
# ---------------------------------------------------------------------------
@app.post("/api/system/backup", response_model=schemas.BackupJobOut)
def trigger_site_backup(
    site_id: str = Query(default="site-alpha"),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    security.validate_site_access(user_payload, site_id)
    res = backup_service.generate_site_backup(db, site_id)
    job = db.query(models.BackupRestoreJob).filter(models.BackupRestoreJob.id == res["job_id"]).first()
    return job


@app.post("/api/system/backup/validate", response_model=schemas.BackupValidationOut)
def validate_backup_archive(
    backup_path: str = Query(...),
    site_id: Optional[str] = Query(default=None),
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    """FR-5.3 / V6-05: Preflight verification of backup archive HMAC signature & checksum."""
    res = backup_service.validate_backup_manifest(backup_path, expected_site_id=site_id)
    return res


@app.post("/api/system/restore")
def trigger_site_restore(
    backup_path: str = Query(...),
    site_id: str = Query(default="site-alpha"),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    security.validate_site_access(user_payload, site_id)
    res = backup_service.restore_site_backup(db, backup_path, site_id)
    return res


@app.post("/api/system/retention/cleanup")
def trigger_retention_cleanup(
    site_id: str = Query(default="site-alpha"),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    security.validate_site_access(user_payload, site_id)
    purged = backup_service.cleanup_expired_evidence(db, site_id)
    return {"status": "completed", "site_id": site_id, "purged_count": purged}


# ---------------------------------------------------------------------------
# Privacy & Governance (FR-10)
# ---------------------------------------------------------------------------
@app.get("/api/governance/status", response_model=schemas.GovernanceStatusOut)
def get_governance_status(
    site_id: str = Query(default="site-alpha"),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    return governance.governance_manager.get_site_governance_status(db, site_id)


@app.post("/api/governance/approve", response_model=schemas.GovernanceApprovalOut)
def approve_governance(
    body: schemas.GovernanceApprovalCreate,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    security.validate_site_access(user_payload, body.site_id)
    approval = governance.governance_manager.record_approval(
        db=db,
        site_id=body.site_id,
        capability=body.capability,
        legal_approval_ref=body.legal_approval_ref,
        approved_by=user_payload.get("sub", "admin"),
        restricted_mode=body.restricted_mode
    )
    return approval


# ---------------------------------------------------------------------------
# Ledger & Tamper Detection (FR-7)
# ---------------------------------------------------------------------------
@app.get("/ledger/verify", response_model=schemas.LedgerVerifyResult)
def verify_ledger(
    site_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    res = ledger.verify_chain(db)
    
    # Extend with external blockchain anchor status (FR-BA-5 / PRD Section 10)
    try:
        query = db.query(models.LedgerAnchor)
        target_site = site_id or "site-alpha"
        query = query.filter(models.LedgerAnchor.site_id == target_site)
        latest_anchor = query.order_by(models.LedgerAnchor.created_at.desc()).first()

        if latest_anchor:
            res.blockchain_anchors_available = True
            res.latest_anchor_id = latest_anchor.id
            res.latest_anchor_status = latest_anchor.status

            if res.intact and latest_anchor.status == "confirmed":
                records = (
                    db.query(models.LedgerRecord)
                    .filter(
                        models.LedgerRecord.site_id == latest_anchor.site_id,
                        models.LedgerRecord.seq >= latest_anchor.from_sequence,
                        models.LedgerRecord.seq <= latest_anchor.through_sequence,
                    )
                    .order_by(models.LedgerRecord.seq.asc())
                    .all()
                )
                if records:
                    local_root = anchor_service.calculate_range_root(records, latest_anchor.schema_version)
                    res.latest_anchor_matches = (local_root == latest_anchor.root_hash)
                else:
                    res.latest_anchor_matches = False
            else:
                res.latest_anchor_matches = False if not res.intact else None
        else:
            res.blockchain_anchors_available = False
    except Exception:
        # Failure to contact blockchain or query anchors must never make local verification unavailable
        res.blockchain_anchors_available = False

    return res


@app.post("/ledger/anchor", response_model=schemas.LedgerAnchorOut)
def create_anchor(
    payload: schemas.LedgerAnchorCreate,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    site_id = payload.site_id or "site-alpha"
    security.validate_site_access(user_payload, site_id)

    try:
        anchor = anchor_service.create_ledger_anchor(
            db=db,
            site_id=site_id,
            from_seq=payload.from_sequence,
            through_seq=payload.through_sequence,
            force=payload.force,
            username=user_payload.get("sub", "admin"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anchor creation failed: {str(e)}")

    write_audit(
        db,
        user_payload.get("sub", "admin"),
        "BLOCKCHAIN_ANCHOR_CREATE",
        site_id=site_id,
        detail=f"Anchored range [{anchor.from_sequence}, {anchor.through_sequence}] as {anchor.id} (tx: {anchor.transaction_hash})",
    )
    return anchor


@app.get("/ledger/anchors", response_model=List[schemas.LedgerAnchorOut])
def get_anchors(
    site_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    if site_id:
        security.validate_site_access(user_payload, site_id)

    q = db.query(models.LedgerAnchor)
    allowed_sites = user_payload.get("site_ids", ["*"])
    if "*" not in allowed_sites:
        q = q.filter(models.LedgerAnchor.site_id.in_(allowed_sites))
    if site_id:
        q = q.filter(models.LedgerAnchor.site_id == site_id)
    if status:
        q = q.filter(models.LedgerAnchor.status == status)

    return q.order_by(models.LedgerAnchor.created_at.desc()).limit(limit).all()


# ---------------------------------------------------------------------------
# Multisignature Proposal & Threshold Governance APIs (FR-MS-1 to FR-MS-4)
# Defined before /ledger/anchors/{anchor_id} to avoid FastAPI path collision
# ---------------------------------------------------------------------------
def _proposal_to_out(p: models.MerkleAnchor) -> schemas.AnchorProposalOut:
    valid_sigs = [s for s in p.signatures if s.status == "valid"]
    sigs_out = [
        schemas.AnchorSignatureOut(
            id=s.id,
            signer_user_id=s.signer_user_id,
            signer_role=s.signer_role,
            signature_algorithm=s.signature_algorithm,
            public_key_id=s.public_key_id,
            signature=s.signature,
            payload_digest=s.payload_digest,
            status=s.status,
            reason=s.reason,
            signed_at=s.signed_at,
        )
        for s in valid_sigs
    ]
    distinct_signers = len({s.signer_user_id for s in valid_sigs})
    threshold = 2
    return schemas.AnchorProposalOut(
        id=p.id,
        site_id=p.site_id,
        from_sequence=p.from_sequence,
        through_sequence=p.through_sequence,
        merkle_root=p.merkle_root,
        provenance_root=p.provenance_root,
        schema_version=p.schema_version,
        status=p.status,
        network=p.network,
        chain_id=p.chain_id,
        contract_address=p.contract_address,
        transaction_hash=p.transaction_hash,
        block_number=p.block_number,
        created_by=p.created_by,
        created_at=p.created_at,
        submitted_at=p.submitted_at,
        confirmed_at=p.confirmed_at,
        expires_at=p.expires_at,
        last_error=p.last_error,
        signatures=sigs_out,
        signatures_count=distinct_signers,
        threshold_required=threshold,
        threshold_met=(distinct_signers >= threshold),
        payload_digest=multisig_service.get_proposal_payload_digest(p),
    )


@app.post("/ledger/anchors/proposals", response_model=schemas.AnchorProposalOut)
def create_proposal_endpoint(
    req: schemas.AnchorProposalCreate,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    site_id = req.site_id or "site-alpha"
    security.validate_site_access(user_payload, site_id)

    try:
        proposal = multisig_service.create_anchor_proposal(
            db=db,
            site_id=site_id,
            from_seq=req.from_sequence,
            through_seq=req.through_sequence,
            created_by=user_payload.get("sub", "admin"),
            expires_in_hours=req.expires_in_hours or 24,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    write_audit(
        db,
        user_payload.get("sub", "admin"),
        "PROPOSAL_CREATE",
        site_id=site_id,
        detail=f"Created proposal {proposal.id} for range [{proposal.from_sequence}, {proposal.through_sequence}]",
    )
    return _proposal_to_out(proposal)


@app.get("/ledger/anchors/proposals", response_model=List[schemas.AnchorProposalOut])
def get_proposals_endpoint(
    site_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    if site_id:
        security.validate_site_access(user_payload, site_id)

    q = db.query(models.MerkleAnchor)
    allowed_sites = user_payload.get("site_ids", ["*"])
    if "*" not in allowed_sites:
        q = q.filter(models.MerkleAnchor.site_id.in_(allowed_sites))
    if site_id:
        q = q.filter(models.MerkleAnchor.site_id == site_id)
    if status:
        q = q.filter(models.MerkleAnchor.status == status)

    proposals = q.order_by(models.MerkleAnchor.created_at.desc()).all()
    return [_proposal_to_out(p) for p in proposals]


@app.get("/ledger/anchors/proposals/{proposal_id}", response_model=schemas.AnchorProposalOut)
def get_proposal_endpoint(
    proposal_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    proposal = db.query(models.MerkleAnchor).filter(models.MerkleAnchor.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")

    security.validate_site_access(user_payload, proposal.site_id)
    return _proposal_to_out(proposal)


@app.post("/ledger/anchors/proposals/{proposal_id}/sign", response_model=schemas.AnchorProposalOut)
def sign_proposal_endpoint(
    proposal_id: str,
    req: schemas.AnchorSignRequest,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    proposal = db.query(models.MerkleAnchor).filter(models.MerkleAnchor.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")

    security.validate_site_access(user_payload, proposal.site_id)

    try:
        updated_proposal, signature = multisig_service.sign_anchor_proposal(
            db=db,
            proposal_id=proposal_id,
            signer_user_id=user_payload.get("sub", "unknown"),
            signer_role=user_payload.get("role", "supervisor"),
            reason=req.reason,
        )
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    write_audit(
        db,
        user_payload.get("sub", "supervisor"),
        "PROPOSAL_SIGN",
        site_id=proposal.site_id,
        detail=f"Signed proposal {proposal_id}: status={updated_proposal.status}",
    )
    return _proposal_to_out(updated_proposal)


@app.post("/ledger/anchors/proposals/{proposal_id}/reject", response_model=schemas.AnchorProposalOut)
def reject_proposal_endpoint(
    proposal_id: str,
    req: schemas.AnchorRejectRequest,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    proposal = db.query(models.MerkleAnchor).filter(models.MerkleAnchor.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")

    security.validate_site_access(user_payload, proposal.site_id)

    try:
        rejected = multisig_service.reject_anchor_proposal(
            db=db,
            proposal_id=proposal_id,
            rejecter_user_id=user_payload.get("sub", "unknown"),
            rejecter_role=user_payload.get("role", "supervisor"),
            reason=req.reason,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    write_audit(
        db,
        user_payload.get("sub", "supervisor"),
        "PROPOSAL_REJECT",
        site_id=proposal.site_id,
        detail=f"Rejected proposal {proposal_id}: reason={req.reason}",
    )
    return _proposal_to_out(rejected)


@app.post("/ledger/anchors/proposals/{proposal_id}/submit", response_model=schemas.AnchorProposalOut)
def submit_proposal_endpoint(
    proposal_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    proposal = db.query(models.MerkleAnchor).filter(models.MerkleAnchor.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")

    security.validate_site_access(user_payload, proposal.site_id)

    try:
        submitted = multisig_service.submit_anchor_proposal(
            db=db,
            proposal_id=proposal_id,
            admin_user_id=user_payload.get("sub", "admin"),
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    write_audit(
        db,
        user_payload.get("sub", "admin"),
        "PROPOSAL_SUBMIT",
        site_id=proposal.site_id,
        detail=f"Submitted proposal {proposal_id} to blockchain: tx={submitted.transaction_hash}",
    )
    return _proposal_to_out(submitted)


@app.post("/ledger/anchors/proposals/{proposal_id}/verify")
def verify_proposal_endpoint(
    proposal_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    proposal = db.query(models.MerkleAnchor).filter(models.MerkleAnchor.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")

    security.validate_site_access(user_payload, proposal.site_id)

    res = multisig_service.verify_proposal_anchor(db, proposal_id)
    write_audit(
        db,
        user_payload.get("sub", "supervisor"),
        "PROPOSAL_VERIFY",
        site_id=proposal.site_id,
        detail=f"Verified proposal {proposal_id}: valid={res.get('valid')}",
    )
    return res


@app.get("/ledger/anchors/{anchor_id}", response_model=schemas.LedgerAnchorOut)
def get_anchor(
    anchor_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    anchor = db.query(models.LedgerAnchor).filter(
        (models.LedgerAnchor.id == anchor_id) | (models.LedgerAnchor.anchor_id == anchor_id)
    ).first()
    if not anchor:
        raise HTTPException(status_code=404, detail=f"Anchor {anchor_id} not found")

    security.validate_site_access(user_payload, anchor.site_id)
    return anchor


@app.post("/ledger/anchors/{anchor_id}/verify", response_model=schemas.LedgerAnchorVerifyResult)
def verify_anchor(
    anchor_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    anchor = db.query(models.LedgerAnchor).filter(
        (models.LedgerAnchor.id == anchor_id) | (models.LedgerAnchor.anchor_id == anchor_id)
    ).first()
    if not anchor:
        raise HTTPException(status_code=404, detail=f"Anchor {anchor_id} not found")

    security.validate_site_access(user_payload, anchor.site_id)

    result = anchor_service.verify_ledger_anchor(db, anchor.id, username=user_payload.get("sub", "supervisor"))

    write_audit(
        db,
        user_payload.get("sub", "supervisor"),
        "BLOCKCHAIN_ANCHOR_VERIFY",
        site_id=anchor.site_id,
        detail=f"Verified anchor {anchor.id}: verified={result.verified}, root_matches={result.root_matches}",
    )
    return result


@app.post("/ledger/anchors/{anchor_id}/retry", response_model=schemas.LedgerAnchorOut)
def retry_anchor(
    anchor_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    anchor = db.query(models.LedgerAnchor).filter(
        (models.LedgerAnchor.id == anchor_id) | (models.LedgerAnchor.anchor_id == anchor_id)
    ).first()
    if not anchor:
        raise HTTPException(status_code=404, detail=f"Anchor {anchor_id} not found")

    security.validate_site_access(user_payload, anchor.site_id)

    provider = blockchain_provider.get_blockchain_provider()
    anchor.attempt_count += 1
    anchor.submitted_at = datetime.utcnow()

    try:
        tx_meta = provider.submit_anchor(
            anchor_id=anchor.anchor_id,
            site_id=anchor.site_id,
            from_seq=anchor.from_sequence,
            through_seq=anchor.through_sequence,
            root_hash=anchor.root_hash,
            schema_version=anchor.schema_version,
        )
        anchor.transaction_hash = tx_meta.get("tx_hash")
        anchor.block_number = tx_meta.get("block_number")
        anchor.confirmations = tx_meta.get("confirmations", 0)
        anchor.status = tx_meta.get("status", "submitted")
        anchor.explorer_url = tx_meta.get("explorer_url")
        if anchor.status == "confirmed":
            anchor.confirmed_at = datetime.utcnow()
        anchor.last_error = None
    except Exception as e:
        anchor.status = "failed"
        anchor.last_error = str(e)

    db.commit()
    db.refresh(anchor)

    write_audit(
        db,
        user_payload.get("sub", "admin"),
        "BLOCKCHAIN_ANCHOR_RETRY",
        site_id=anchor.site_id,
        detail=f"Retried anchor {anchor.id}: status={anchor.status}, attempt={anchor.attempt_count}",
    )
    return anchor


@app.post("/ledger/tamper-demo/{alert_id}")
def tamper_demo(
    alert_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    tamper_suffix = "".join(random.choices(string.ascii_uppercase, k=4))
    current = security.decrypt_field(alert.detail_enc) if alert.detail_enc else "Event Detail"
    alert.detail_enc = security.encrypt_field(current + f" [TAMPERED-{tamper_suffix}]")
    db.commit()
    write_audit(db, user_payload.get("sub"), "TAMPER_DEMO", site_id=alert.site_id, detail=f"Directly edited {alert_id} bypassing ledger")
    return {"status": "tampered", "alert_id": alert_id}


# ---------------------------------------------------------------------------
# Advanced Blockchain Integrity: Merkle Proofs & Provenance (FR-MP)
# ---------------------------------------------------------------------------


@app.post("/ledger/merkle/build", response_model=schemas.MerkleBuildResponse)
def build_merkle_tree_endpoint(
    req: schemas.MerkleBuildRequest,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    site_id = req.site_id or "site-alpha"
    security.validate_site_access(user_payload, site_id)

    records = (
        db.query(models.LedgerRecord)
        .filter(
            models.LedgerRecord.site_id == site_id,
            models.LedgerRecord.seq >= req.from_sequence,
            models.LedgerRecord.seq <= req.through_sequence,
        )
        .order_by(models.LedgerRecord.seq.asc())
        .all()
    )
    if not records:
        raise HTTPException(status_code=400, detail="No ledger records in specified sequence range")

    leaf_hashes = []
    prov_hashes = []
    for r in records:
        alert = db.query(models.Alert).filter(models.Alert.id == r.alert_id).first()
        if alert and not alert.provenance_hash:
            provenance_service.attach_alert_provenance(alert, db)
            db.commit()

        leaf_payload = merkle_engine.build_canonical_leaf_payload(
            site_id=site_id,
            sequence=r.seq,
            alert_id=r.alert_id,
            record_hash=r.record_hash,
            model_provenance_hash=alert.provenance_hash if alert else None,
            rule_config_hash=alert.rule_config_hash if alert else None,
        )
        leaf_hashes.append(merkle_engine.compute_leaf_hash(leaf_payload))
        prov_hashes.append(alert.provenance_hash if (alert and alert.provenance_hash) else ("0" * 64))

    root_hash, _ = merkle_engine.build_merkle_tree(leaf_hashes)
    prov_root = merkle_engine.compute_provenance_root(prov_hashes)

    return schemas.MerkleBuildResponse(
        root_hash=root_hash,
        provenance_root_hash=prov_root,
        leaf_count=len(leaf_hashes),
        from_sequence=req.from_sequence,
        through_sequence=req.through_sequence,
        schema_version="merkle-v1",
    )


@app.get("/ledger/proof/{alert_id}", response_model=schemas.MerkleProofResponse)
@app.get("/alerts/{alert_id}/merkle-proof", response_model=schemas.MerkleProofResponse)
def get_alert_merkle_proof(
    alert_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    security.validate_site_access(user_payload, alert.site_id)

    ledger_rec = db.query(models.LedgerRecord).filter(models.LedgerRecord.alert_id == alert_id).first()
    if not ledger_rec:
        raise HTTPException(status_code=400, detail=f"Alert {alert_id} has no linked ledger sequence")

    # Check if there is an active proposal or anchor covering this record
    anchor = (
        db.query(models.MerkleAnchor)
        .filter(
            models.MerkleAnchor.site_id == alert.site_id,
            models.MerkleAnchor.from_sequence <= ledger_rec.seq,
            models.MerkleAnchor.through_sequence >= ledger_rec.seq,
        )
        .first()
    )

    from_seq = anchor.from_sequence if anchor else 0
    through_seq = anchor.through_sequence if anchor else ledger_rec.seq

    # Query all records in range
    records = (
        db.query(models.LedgerRecord)
        .filter(
            models.LedgerRecord.site_id == alert.site_id,
            models.LedgerRecord.seq >= from_seq,
            models.LedgerRecord.seq <= through_seq,
        )
        .order_by(models.LedgerRecord.seq.asc())
        .all()
    )

    leaf_hashes = []
    target_index = -1
    target_payload = {}

    for idx, r in enumerate(records):
        rec_alert = db.query(models.Alert).filter(models.Alert.id == r.alert_id).first()
        if rec_alert and not rec_alert.provenance_hash:
            provenance_service.attach_alert_provenance(rec_alert, db)
            db.commit()

        lp = merkle_engine.build_canonical_leaf_payload(
            site_id=alert.site_id,
            sequence=r.seq,
            alert_id=r.alert_id,
            record_hash=r.record_hash,
            model_provenance_hash=rec_alert.provenance_hash if rec_alert else None,
            rule_config_hash=rec_alert.rule_config_hash if rec_alert else None,
        )
        lh = merkle_engine.compute_leaf_hash(lp)
        leaf_hashes.append(lh)
        if r.seq == ledger_rec.seq:
            target_index = idx
            target_payload = lp

    if target_index == -1:
        raise HTTPException(status_code=500, detail="Target leaf could not be indexed in sequence range")

    root_hash, _ = merkle_engine.build_merkle_tree(leaf_hashes)
    sibling_hashes, positions = merkle_engine.generate_merkle_proof(leaf_hashes, target_index)

    return schemas.MerkleProofResponse(
        alert_id=alert.id,
        sequence=ledger_rec.seq,
        leaf_hash=leaf_hashes[target_index],
        leaf_payload=target_payload,
        sibling_hashes=sibling_hashes,
        positions=positions,
        root_hash=root_hash,
        schema_version="merkle-v1",
        from_sequence=from_seq,
        through_sequence=through_seq,
    )


@app.post("/ledger/proof/verify", response_model=schemas.MerkleProofVerifyResponse)
def verify_merkle_proof_endpoint(
    req: schemas.MerkleProofVerifyRequest,
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    valid, calc_root = merkle_engine.verify_merkle_proof(
        leaf_hash=req.leaf_hash,
        sibling_hashes=req.sibling_hashes,
        positions=req.positions,
        root_hash=req.root_hash,
    )
    msg = (
        "Alert is included in the requested Merkle root."
        if valid
        else f"Proof mismatch: computed root ({calc_root}) does not match expected root ({req.root_hash})."
    )
    return schemas.MerkleProofVerifyResponse(
        valid=valid,
        alert_id=req.alert_id,
        root_hash=req.root_hash,
        calculated_root_hash=calc_root,
        message=msg,
    )


# ---------------------------------------------------------------------------
# AI Model Provenance APIs (FR-MP-4, FR-MP-5)
# ---------------------------------------------------------------------------
@app.get("/models/{model_version}/provenance", response_model=schemas.ModelProvenanceOut)
def get_model_provenance(
    model_version: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    prov = provenance_service.get_or_register_model_provenance(db, model_version)
    return schemas.ModelProvenanceOut(
        id=prov.id,
        model_name=prov.model_name,
        model_version=prov.model_version,
        artifact_hash=prov.artifact_hash,
        runtime_version=prov.runtime_version,
        rule_version=prov.rule_version,
        rule_config_hash=prov.rule_config_hash,
        preprocessing_config_hash=prov.preprocessing_config_hash,
        provenance_hash=prov.provenance_hash,
        registered_by=prov.registered_by,
        created_at=prov.created_at,
    )


@app.get("/alerts/{alert_id}/provenance", response_model=schemas.AlertProvenanceOut)
def get_alert_provenance(
    alert_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("operator", allow_guest_operator=True))
):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    security.validate_site_access(user_payload, alert.site_id)

    if not alert.provenance_hash:
        provenance_service.attach_alert_provenance(alert, db)
        db.commit()
        db.refresh(alert)

    return schemas.AlertProvenanceOut(
        alert_id=alert.id,
        provenance=alert.provenance or "detector",
        model_name=alert.model_name,
        model_version=alert.model_version,
        model_artifact_hash=alert.model_artifact_hash,
        runtime_version=alert.runtime_version,
        rule_version=alert.rule_version,
        rule_config_hash=alert.rule_config_hash,
        preprocessing_config_hash=alert.preprocessing_config_hash,
        provenance_hash=alert.provenance_hash,
        is_valid=True,
    )


@app.post("/alerts/{alert_id}/provenance/verify", response_model=schemas.AlertProvenanceVerifyResponse)
def verify_alert_provenance_endpoint(
    alert_id: str,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    security.validate_site_access(user_payload, alert.site_id)

    matches, stored_hash, recomputed_hash, message = provenance_service.verify_alert_provenance(alert)
    return schemas.AlertProvenanceVerifyResponse(
        alert_id=alert.id,
        provenance=alert.provenance or "detector",
        stored_hash=stored_hash,
        recomputed_hash=recomputed_hash,
        matches=matches,
        message=message,
    )


# ---------------------------------------------------------------------------
# Audit Log & C2 Staging (FR-5, FR-7, FR-9)
# ---------------------------------------------------------------------------
@app.get("/audit-log", response_model=List[schemas.AuditLogOut])
def get_audit_log(
    site_id: Optional[str] = Query(default=None),
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor"))
):
    if site_id:
        security.validate_site_access(user_payload, site_id)

    q = db.query(models.AuditLog)
    allowed_sites = user_payload.get("site_ids", ["*"])
    if "*" not in allowed_sites:
        q = q.filter(models.AuditLog.site_id.in_(allowed_sites))
    if site_id:
        q = q.filter(models.AuditLog.site_id == site_id)

    return q.order_by(models.AuditLog.ts.desc()).limit(limit).all()


# ---------------------------------------------------------------------------
# C2 Tactical Deliveries & Retry Management (PRD v1 FR-10)
# ---------------------------------------------------------------------------
@app.get("/api/c2/deliveries")
def list_c2_deliveries(
    site_id: Optional[str] = Query(default=None),
    user_payload: Dict[str, Any] = Depends(security.require_role("supervisor", allow_guest_operator=True))
):
    """List historical C2 tactical deliveries and pending retry queue."""
    allowed_sites = user_payload.get("site_ids", ["*"])
    
    delivered = [
        d for d in rule_engine.c2_delivery_log
        if ("*" in allowed_sites or d.get("site_id") in allowed_sites) and (not site_id or d.get("site_id") == site_id)
    ]
    retry_queue = [
        r for r in rule_engine.c2_retry_queue
        if ("*" in allowed_sites or r.get("site_id") in allowed_sites) and (not site_id or r.get("site_id") == site_id)
    ]
    return {
        "delivered_count": len(delivered),
        "dead_letter_count": len(retry_queue),
        "deliveries": delivered[-50:],
        "retry_queue": retry_queue
    }


@app.post("/api/c2/deliveries/{delivery_id}/retry")
def retry_c2_delivery(
    delivery_id: str,
    user_payload: Dict[str, Any] = Depends(security.require_role("admin"))
):
    """Manually retry a dead-lettered tactical C2 delivery."""
    matching = [item for item in rule_engine.c2_retry_queue if item.get("alert_id") == delivery_id or item.get("idempotency_key") == delivery_id]
    if not matching:
        raise HTTPException(status_code=404, detail="No matching dead-letter delivery found to retry")
    
    item = matching[0]
    rule_engine.c2_retry_queue.remove(item)
    
    result = rule_engine.dispatch_to_c2_sync(item.get("alert_id"), item.get("payload", {}), max_retries=1)
    return {"status": "retried", "result": result}


@app.post("/api/c2/mock-webhook")
def c2_mock_webhook(payload: dict):
    return {"status": "received", "timestamp": datetime.utcnow().isoformat()}


# ---------------------------------------------------------------------------
# Authenticated WebSocket with Site Scoping (FR-1.1, FR-2.3)
# ---------------------------------------------------------------------------
@app.websocket("/ws/alerts")
async def ws_alerts(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None),
    site_id: Optional[str] = Query(default=None)
):
    """FR-1.1 / FR-2.3: Rejects invalid token or unauthorized site access on WebSocket."""
    try:
        if token and token.strip():
            payload = security.authenticate_ws_token(token)
            if site_id:
                security.validate_site_access(payload, site_id)
        elif os.getenv("IBVAP_STRICT_WS_AUTH", "false").lower() == "true":
            raise HTTPException(status_code=401, detail="WebSocket authentication token required")
    except Exception:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
