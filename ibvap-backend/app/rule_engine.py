"""
Rule Engine and C2 Tactical Integration Adapter for IBVAP (PRD v4 FR-4, FR-5, FR-8).
Evaluates virtual fence lines and polygon zones with cooldown deduplication,
creates EvidenceAsset records, and dispatches real signed HTTP payloads to C2 network.
"""
import os
import time
import random
import base64
import logging
import hashlib
import hmac
import secrets
import json
import urllib.request
import urllib.error
from datetime import datetime
import asyncio
from typing import List, Dict, Tuple, Optional, Any
from sqlalchemy.orm import Session

from . import models, schemas, security, ledger
from .database import SessionLocal
from .ws_manager import manager
from .tracker import Track

logger = logging.getLogger("ibvap.rules")

# C2 Secret Key for HMAC-SHA256 signature signing (FR-5.2)
C2_SECRET_KEY = os.getenv("IBVAP_C2_SECRET", "ibvap-tactical-c2-shared-key")
C2_WEBHOOK_URL = os.getenv("IBVAP_C2_URL", "http://localhost:8000/api/c2/mock-webhook")

# Cooldown tracking: (camera_id, rule_id, track_id) -> timestamp
_cooldown_tracker: Dict[Tuple[str, str, str], float] = {}

# C2 dead-letter / retry queue for resilient delivery (FR-5.5)
c2_retry_queue: List[Dict] = []
c2_delivery_log: List[Dict] = []


def generate_alert_id() -> str:
    """Collision-resistant ID generation for concurrent writers (FR-7.3)."""
    now = datetime.utcnow()
    rand_suffix = secrets.token_hex(6).upper()
    return f"EVT-{now.strftime('%Y%m%d%H%M%S')}-{rand_suffix}"


# ---------------------------------------------------------------------------
# Geometry Utilities for Virtual Fence (FR-4.2)
# ---------------------------------------------------------------------------
def _ccw(A: List[float], B: List[float], C: List[float]) -> bool:
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])


def line_intersect(A: List[float], B: List[float], C: List[float], D: List[float]) -> bool:
    """Returns True if line segment AB intersects line segment CD."""
    return (_ccw(A, C, D) != _ccw(B, C, D)) and (_ccw(A, B, C) != _ccw(A, B, D))


def point_in_polygon(point: List[float], polygon: List[List[float]]) -> bool:
    """Ray casting algorithm to determine if point [x, y] is inside polygon."""
    x, y = point[0], point[1]
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def is_in_cooldown(camera_id: str, rule_id: str, track_id: str, cooldown_seconds: int) -> bool:
    key = (camera_id, rule_id, track_id)
    now = time.time()
    last_triggered = _cooldown_tracker.get(key, 0.0)
    if (now - last_triggered) < cooldown_seconds:
        return True
    _cooldown_tracker[key] = now
    return False


_seen_c2_idempotency_keys: Dict[str, float] = {}


def verify_c2_replay(idempotency_key: str, timestamp_str: str, max_drift_sec: float = 300.0) -> Tuple[bool, str]:
    """FR-7.5 / V5-07: Validates timestamp drift and prevents replay attacks."""
    now = time.time()
    if idempotency_key in _seen_c2_idempotency_keys:
        return False, "Duplicate idempotency key rejected (replay protection)"

    try:
        ts_dt = datetime.fromisoformat(timestamp_str)
        drift = abs((datetime.utcnow() - ts_dt).total_seconds())
        if drift > max_drift_sec:
            return False, f"Timestamp drift ({drift:.1f}s) exceeds allowed threshold of {max_drift_sec}s"
    except Exception:
        return False, "Invalid timestamp format"

    _seen_c2_idempotency_keys[idempotency_key] = now
    if len(_seen_c2_idempotency_keys) > 1000:
        for k in list(_seen_c2_idempotency_keys.keys())[:200]:
            if (now - _seen_c2_idempotency_keys[k]) > 600:
                del _seen_c2_idempotency_keys[k]
    return True, "Valid"


def sign_c2_payload(payload_json: str) -> str:
    """HMAC-SHA256 signing for C2 tactical events (FR-5.2)."""
    return hmac.new(
        C2_SECRET_KEY.encode("utf-8"),
        payload_json.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def dispatch_to_c2_sync(alert_id: str, payload_dict: Dict, max_retries: int = 2) -> Dict:
    """
    FR-5.3 / FR-7.3: Real HTTP delivery with timeout, HMAC signing,
    idempotency header, and dead-letter queue tracking.
    """
    site_id = payload_dict.get("site_id", "site-alpha")
    payload_dict["site_id"] = site_id
    payload_json = json.dumps(payload_dict, sort_keys=True)
    signature = sign_c2_payload(payload_json)
    idempotency_key = f"IDEMP-{alert_id}"

    headers = {
        "Content-Type": "application/json",
        "X-IBVAP-Signature": signature,
        "X-IBVAP-Idempotency-Key": idempotency_key,
        "X-IBVAP-Timestamp": datetime.utcnow().isoformat(),
        "X-IBVAP-Site-ID": site_id
    }

    req = urllib.request.Request(
        C2_WEBHOOK_URL,
        data=payload_json.encode("utf-8"),
        headers=headers,
        method="POST"
    )

    attempt = 0
    while attempt <= max_retries:
        attempt += 1
        try:
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                status_code = resp.status
                body = resp.read().decode("utf-8")
                record = {
                    "alert_id": alert_id,
                    "site_id": site_id,
                    "status": "delivered",
                    "http_status": status_code,
                    "idempotency_key": idempotency_key,
                    "signature": signature,
                    "timestamp": datetime.utcnow().isoformat(),
                    "attempts": attempt
                }
                c2_delivery_log.append(record)
                logger.info(f"[C2 DELIVERY SUCCESS] Alert {alert_id} delivered to C2 (Attempt {attempt}, Status {status_code})")
                return record
        except Exception as ex:
            logger.warning(f"[C2 DELIVERY ATTEMPT {attempt} FAILED] {ex}")
            if attempt > max_retries:
                dead_letter = {
                    "alert_id": alert_id,
                    "site_id": site_id,
                    "status": "dead_letter",
                    "last_error": str(ex),
                    "idempotency_key": idempotency_key,
                    "payload": payload_dict,
                    "next_retry": time.time() + 60.0,
                    "attempts": attempt
                }
                c2_retry_queue.append(dead_letter)
                logger.error(f"[C2 DEAD-LETTER] Moved alert {alert_id} to dead-letter queue for background retry.")
                return dead_letter
            time.sleep(0.5)


# ---------------------------------------------------------------------------
# Rule Evaluation & Evidence Creation (FR-4, FR-8)
# ---------------------------------------------------------------------------
def evaluate_track_against_rules_sync(
    db: Session,
    camera: models.Camera,
    track: Track,
    frame_bytes: Optional[bytes] = None
) -> Optional[models.Alert]:
    """
    Synchronous evaluation of tracks against camera fence rules.
    Creates Alert, EvidenceAsset, LedgerRecord, and triggers C2 dispatch.
    """
    rules = db.query(models.FenceRule).filter(
        models.FenceRule.camera_id == camera.id,
        models.FenceRule.enabled == True
    ).all()

    if not rules:
        return None

    now_ts = datetime.utcnow()

    for rule in rules:
        if rule.target_classes and track.class_name not in rule.target_classes:
            continue

        triggered = False
        trigger_reason = ""

        # Tripwire evaluation
        if rule.rule_type == "tripwire" and len(rule.coordinates) >= 2:
            wire_start = rule.coordinates[0]
            wire_end = rule.coordinates[1]

            if len(track.history) >= 2:
                prev_pos = track.history[-2]
                curr_pos = track.history[-1]

                if line_intersect(prev_pos, curr_pos, wire_start, wire_end):
                    triggered = True
                    trigger_reason = f"Tripwire '{rule.name}' crossed by {track.class_name} ({track.track_id})"

        # Polygon zone evaluation
        elif rule.rule_type in ("polygon_zone", "loiter_zone") and len(rule.coordinates) >= 3:
            curr_pos = track.centroid
            if point_in_polygon(curr_pos, rule.coordinates):
                if rule.rule_type == "loiter_zone":
                    if track.dwell_time >= 4.0:
                        triggered = True
                        trigger_reason = f"Loitering in '{rule.name}' for {int(track.dwell_time)}s by {track.class_name} ({track.track_id})"
                else:
                    triggered = True
                    trigger_reason = f"Zone '{rule.name}' breached by {track.class_name} ({track.track_id})"

        if triggered:
            # Blue-Force / Friendly Army Patrol De-escalation:
            # Verified military personnel on routine patrol do not trigger intrusion alerts
            if getattr(track, "is_friendly", False):
                logger.info(f"[RuleEngine] De-escalated intrusion: Friendly Army patrol detected ({track.track_id}) in rule '{rule.name}'")
                continue

            # Animal-Class False-Positive Suppression (Review P1):
            # Wildlife and stray cattle (cow, dog, sheep, bird) are treated as informational activity,
            # avoiding perimeter siren false alarms while keeping the sentry aware.
            if getattr(track, "is_animal", False) or track.class_name in ("cow", "dog", "horse", "sheep", "bird", "cat"):
                logger.info(f"[RuleEngine] Animal activity suppressed from perimeter siren: {track.class_name} ({track.track_id})")
                continue

            if is_in_cooldown(camera.id, rule.id, track.track_id, rule.cooldown_seconds):
                continue

            alert_id = generate_alert_id()

            # Infiltration Crawling Posture Check (Review P2):
            is_crawling = getattr(track, "is_crawling", False)
            if is_crawling:
                trigger_reason += " [TACTICAL INFILTRATION: Low-profile crawling posture detected]"
                alert_type = "crawling_infiltration"
            else:
                alert_type = "intrusion" if rule.rule_type != "loiter_zone" else "loiter"

            # Process evidence snapshot & SHA-256 hash (FR-8.1, FR-8.2)
            snapshot_data_url = None
            content_hash = ""
            encrypted_snapshot = None

            if frame_bytes:
                content_hash = hashlib.sha256(frame_bytes).hexdigest()
                snapshot_data_url = f"data:image/jpeg;base64,{base64.b64encode(frame_bytes).decode('ascii')}"
                encrypted_snapshot = security.encrypt_field(snapshot_data_url)

            site_id = getattr(camera, "site_id", "site-alpha") or "site-alpha"

            # 1. Create Alert record
            alert = models.Alert(
                id=alert_id,
                site_id=site_id,
                type=alert_type,
                sev="critical" if is_crawling else rule.severity,
                cam_id=camera.id,
                cam_name=camera.name,
                location=camera.location,
                confidence=int(round(track.confidence * 100)) if track.confidence <= 1.0 else int(track.confidence),
                track_id=track.track_id,
                detail_enc=security.encrypt_field(trigger_reason),
                reviewed=False,
                state="open",
                provenance="detector",
                model_version="8.2.0",
                rule_id=rule.id,
                rule_version=getattr(rule, "version", "1.0"),
                source_frame_time=now_ts,
                evidence_hash=content_hash if content_hash else None,
                ts=now_ts,
                snapshot_enc=encrypted_snapshot,
            )
            db.add(alert)

            # 2. Create EvidenceAsset record (FR-8.1)
            if frame_bytes and encrypted_snapshot:
                evidence_asset = models.EvidenceAsset(
                    id=f"EVD-{alert_id}",
                    site_id=site_id,
                    alert_id=alert.id,
                    camera_id=camera.id,
                    asset_type="snapshot",
                    content_hash=content_hash,
                    encrypted_data=encrypted_snapshot,
                    captured_at=now_ts,
                )
                db.add(evidence_asset)

            db.commit()
            db.refresh(alert)

            # 3. Append to SHA-256 Ledger
            ledger.append_to_ledger(db, alert)

            # 3b. GIS Terrain Enrichment & Tactical Recommendation (PRD v1 FR-6, FR-7)
            try:
                from . import terrain_service, recommendation_service
                terrain = terrain_service.enrich_alert_terrain(db, alert)
                recommendation_service.generate_tactical_recommendation(db, alert, terrain)
            except Exception as enrich_ex:
                logger.warning(f"[ENRICHMENT WARNING] Non-blocking terrain/recommendation error: {enrich_ex}")

            # 4. Dispatch to Real C2 Tactical Network
            if rule.severity == "high":
                c2_payload = {
                    "alert_id": alert.id,
                    "site_id": site_id,
                    "type": alert.type,
                    "sev": alert.sev,
                    "camera_id": camera.id,
                    "location": camera.location,
                    "track_id": track.track_id,
                    "timestamp": now_ts.isoformat(),
                    "evidence_hash": content_hash,
                    "provenance": "detector"
                }
                # Dispatch in background thread
                import threading
                threading.Thread(
                    target=dispatch_to_c2_sync,
                    args=(alert.id, c2_payload),
                    daemon=True
                ).start()

            # 5. Broadcast to WebSocket
            out = schemas.AlertOut(
                id=alert.id,
                type=alert.type,
                sev=alert.sev,
                cam_id=alert.cam_id,
                cam_name=alert.cam_name,
                location=alert.location,
                confidence=alert.confidence,
                track_id=alert.track_id,
                detail=trigger_reason,
                reviewed=False,
                state="open",
                provenance="detector",
                rule_id=rule.id,
                rule_version="1.0",
                source_frame_time=now_ts,
                evidence_hash=content_hash,
                ts=alert.ts,
                snapshot=snapshot_data_url
            )
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(manager.broadcast_alert(out.model_dump(by_alias=True)))
            except Exception:
                pass

            logger.info(f"[DETECTOR RULE] Emitted real alert {alert.id} ({alert.type}) on {camera.id}")
            return alert

    return None


def create_tamper_alert_sync(
    db: Session,
    camera: models.Camera,
    tamper_info: Dict[str, Any],
    frame_bytes: Optional[bytes] = None
) -> Optional[models.Alert]:
    """
    Generate an instantaneous SYSTEM / TAMPER alert when lens obstruction, defocus,
    or stream stall is detected (Review Section 3.1).
    """
    rule_key = f"tamper_{tamper_info.get('tamper_type', 'lens_obstruction')}"
    if is_in_cooldown(camera.id, rule_key, "system", 60.0):
        return None

    now_ts = datetime.utcnow()
    alert_id = generate_alert_id()

    snapshot_data_url = None
    content_hash = ""
    encrypted_snapshot = None

    if frame_bytes:
        content_hash = hashlib.sha256(frame_bytes).hexdigest()
        snapshot_data_url = f"data:image/jpeg;base64,{base64.b64encode(frame_bytes).decode('ascii')}"
        encrypted_snapshot = security.encrypt_field(snapshot_data_url)

    site_id = getattr(camera, "site_id", "site-alpha") or "site-alpha"
    detail = f"CAMERA HEALTH / TAMPER DETECTED: {tamper_info.get('detail', 'Sensor anomaly')}"

    alert = models.Alert(
        id=alert_id,
        site_id=site_id,
        type="tamper",
        sev=tamper_info.get("severity", "high"),
        cam_id=camera.id,
        cam_name=camera.name,
        location=camera.location,
        confidence=98,
        track_id="#SYS-TAMPER",
        detail_enc=security.encrypt_field(detail),
        reviewed=False,
        state="open",
        provenance="detector",
        model_version="health-v1.0",
        rule_id="RULE-HEALTH-TAMPER",
        rule_version="1.0",
        source_frame_time=now_ts,
        evidence_hash=content_hash if content_hash else None,
        ts=now_ts,
        snapshot_enc=encrypted_snapshot,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Append to SHA-256 Ledger
    ledger.append_to_ledger(db, alert)

    # Broadcast via WebSocket
    out = schemas.AlertOut(
        id=alert.id,
        type=alert.type,
        sev=alert.sev,
        cam_id=alert.cam_id,
        cam_name=alert.cam_name,
        location=alert.location,
        confidence=alert.confidence,
        track_id=alert.track_id,
        detail=detail,
        reviewed=False,
        state="open",
        provenance="detector",
        rule_id="RULE-HEALTH-TAMPER",
        rule_version="1.0",
        source_frame_time=now_ts,
        evidence_hash=content_hash,
        ts=alert.ts,
        snapshot=snapshot_data_url
    )
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(manager.broadcast_alert(out.model_dump(by_alias=True)))
    except Exception:
        pass

    logger.warning(f"[TAMPER ALERT] Emitted physical tamper alert {alert.id} for {camera.id}: {detail}")
    return alert


async def trigger_periodic_rule_events():
    """Background task generating periodic simulated intelligence events
    tagged with provenance='simulation' per PRD v4 FR-4."""
    from .video_stream import get_camera_frame
    await asyncio.sleep(10)
    while True:
        try:
            await asyncio.sleep(25)
            db: Session = SessionLocal()
            try:
                event_choice = random.choice(["anpr", "watchlist", "intrusion", "loiter"])
                alert_id = generate_alert_id()
                
                if event_choice == "anpr":
                    plate = random.choice(["PB-11-AK-4471", "RJ-06-CT-1183", "HR-26-BQ-7742"])
                    cam = db.query(models.Camera).filter(models.Camera.id == "cam-2").first()
                    if not cam or not cam.online:
                        continue
                    detail = f"ANPR: Vehicle Plate {plate} matched flagged watchlist database"
                    sev = "med"
                    type_ = "anpr"
                    conf = random.randint(88, 97)
                elif event_choice == "watchlist":
                    cam = db.query(models.Camera).filter(models.Camera.id.in_(["cam-2", "cam-3"])).first()
                    if not cam or not cam.online:
                        continue
                    detail = "Match: Watchlist ID WL-009 (Tariq M. — Person of Interest)"
                    sev = "high"
                    type_ = "watchlist"
                    conf = random.randint(91, 98)
                elif event_choice == "intrusion":
                    cam = db.query(models.Camera).filter(models.Camera.id == "cam-3").first()
                    if not cam or not cam.online:
                        continue
                    detail = f"Virtual fence boundary crossed by detected object on {cam.name}"
                    sev = "high"
                    type_ = "intrusion"
                    conf = random.randint(84, 95)
                else:
                    cam = db.query(models.Camera).filter(models.Camera.id == "cam-2").first()
                    if not cam or not cam.online:
                        continue
                    detail = "Loitering detected: Target stationary > 4s near gate boundary"
                    sev = "med"
                    type_ = "loiter"
                    conf = random.randint(82, 93)

                frame_bytes = get_camera_frame(cam.id)
                snapshot_data_url = f"data:image/jpeg;base64,{base64.b64encode(frame_bytes).decode('ascii')}" if frame_bytes else None
                now_ts = datetime.utcnow()

                content_hash = hashlib.sha256(frame_bytes).hexdigest() if frame_bytes else ""
                encrypted_snapshot = security.encrypt_field(snapshot_data_url)

                alert = models.Alert(
                    id=alert_id,
                    type=type_,
                    sev=sev,
                    cam_id=cam.id,
                    cam_name=cam.name,
                    location=cam.location,
                    confidence=conf,
                    track_id=f"#{random.randint(110, 990)}",
                    detail_enc=security.encrypt_field(detail),
                    reviewed=False,
                    state="open",
                    provenance="simulation",
                    rule_id=f"rule-{cam.id}-01",
                    rule_version="1.0",
                    source_frame_time=now_ts,
                    evidence_hash=content_hash,
                    ts=now_ts,
                    snapshot_enc=encrypted_snapshot,
                )
                db.add(alert)

                if frame_bytes and encrypted_snapshot:
                    db.add(models.EvidenceAsset(
                        id=f"EVD-{alert_id}",
                        alert_id=alert.id,
                        camera_id=cam.id,
                        asset_type="snapshot",
                        content_hash=content_hash,
                        encrypted_data=encrypted_snapshot,
                        captured_at=now_ts
                    ))

                db.commit()
                db.refresh(alert)

                ledger.append_to_ledger(db, alert)

                out = schemas.AlertOut(
                    id=alert.id,
                    type=alert.type,
                    sev=alert.sev,
                    cam_id=alert.cam_id,
                    cam_name=alert.cam_name,
                    location=alert.location,
                    confidence=alert.confidence,
                    track_id=alert.track_id,
                    detail=detail,
                    reviewed=False,
                    state="open",
                    provenance="simulation",
                    rule_id=alert.rule_id,
                    rule_version="1.0",
                    source_frame_time=now_ts,
                    evidence_hash=content_hash,
                    ts=alert.ts,
                    snapshot=snapshot_data_url
                )
                await manager.broadcast_alert(out.model_dump(by_alias=True))

            finally:
                db.close()
        except Exception as e:
            logger.error(f"[SIMULATION ERROR]: {e}")
            await asyncio.sleep(5)
