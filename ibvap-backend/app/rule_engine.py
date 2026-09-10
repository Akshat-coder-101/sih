"""
Rule Engine and Background Event Processor for IBVAP.
Handles virtual fence crossing, loiter dwell timer, ANPR plate recognition,
watchlist face matching, and C2 Command & Control webhook dispatch.
"""
import time
import random
import base64
import logging
from datetime import datetime
import asyncio
from sqlalchemy.orm import Session

from . import models, schemas, security, ledger
from .database import SessionLocal
from .ws_manager import manager
from .video_stream import get_camera_frame

logger = logging.getLogger("ibvap.rules")

C2_WEBHOOK_URL = "http://localhost:8000/api/c2/mock-webhook"

# Watchlist database
WATCHLIST = [
    {"id": "WL-009", "name": "Tariq M.", "role": "Person of Interest", "threat": "high"},
    {"id": "WL-014", "name": "Karan S.", "role": "Cross-Border Suspect", "threat": "high"},
    {"id": "WL-021", "name": "Devraj V.", "role": "Smuggling Watchlist", "threat": "high"}
]

ANPR_PLATES = [
    "PB-11-AK-4471",
    "RJ-06-CT-1183",
    "HR-26-BQ-7742",
    "UP-14-DT-9901"
]


def mock_c2_dispatch(alert: models.Alert):
    """Simulates C2 (Command and Control) military dispatch relay."""
    logger.info(f"[C2 RELAY] Dispatched high-severity alert {alert.id} ({alert.type}) to C2 tactical network.")


async def trigger_periodic_rule_events():
    """Background task generating periodic AI intelligence events (ANPR, Watchlist, Fence intrusion)
    on simulated cameras, saving to DB with AES-256 encryption, hashing into ledger, and pushing to WebSocket."""
    # Delay startup slightly
    await asyncio.sleep(10)
    while True:
        try:
            await asyncio.sleep(25)  # Fire realistic event every 25 seconds
            db: Session = SessionLocal()
            try:
                event_choice = random.choice(["anpr", "watchlist", "intrusion", "loiter"])
                count = db.query(models.Alert).count()
                new_id = f"EVT-{count + 1:04d}"
                
                if event_choice == "anpr":
                    plate = random.choice(ANPR_PLATES)
                    cam = db.query(models.Camera).filter(models.Camera.id == "cam-2").first()
                    if not cam or not cam.online:
                        continue
                    detail = f"ANPR: Vehicle Plate {plate} matched flagged watchlist database"
                    sev = "med"
                    type_ = "anpr"
                    conf = random.randint(88, 97)
                elif event_choice == "watchlist":
                    person = random.choice(WATCHLIST)
                    cam = db.query(models.Camera).filter(models.Camera.id.in_(["cam-2", "cam-3"])).first()
                    if not cam or not cam.online:
                        continue
                    detail = f"Match: Watchlist ID {person['id']} ({person['name']} — {person['role']})"
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
                    detail = f"Loitering detected: Target stationary > 4s near gate boundary"
                    sev = "med"
                    type_ = "loiter"
                    conf = random.randint(82, 93)

                # Capture real frame snapshot from video generator
                frame_bytes = get_camera_frame(cam.id)
                snapshot_data_url = f"data:image/jpeg;base64,{base64.b64encode(frame_bytes).decode('ascii')}" if frame_bytes else None

                alert = models.Alert(
                    id=new_id,
                    type=type_,
                    sev=sev,
                    cam_id=cam.id,
                    cam_name=cam.name,
                    location=cam.location,
                    confidence=conf,
                    track_id=f"#{random.randint(110, 990)}",
                    detail_enc=security.encrypt_field(detail),
                    reviewed=False,
                    ts=datetime.utcnow(),
                    snapshot_enc=security.encrypt_field(snapshot_data_url),
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)

                ledger.append_to_ledger(db, alert)

                if sev == "high":
                    mock_c2_dispatch(alert)

                out = schemas.AlertOut(
                    id=alert.id, type=alert.type, sev=alert.sev, cam_id=alert.cam_id,
                    cam_name=alert.cam_name, location=alert.location, confidence=alert.confidence,
                    track_id=alert.track_id, detail=detail, reviewed=alert.reviewed,
                    ts=alert.ts, snapshot=snapshot_data_url
                )
                await manager.broadcast_alert(out.model_dump(by_alias=True))
                logger.info(f"[RULE ENGINE] Generated and broadcast alert {alert.id} ({alert.type})")

            finally:
                db.close()
        except Exception as e:
            logger.error(f"[RULE ENGINE ERROR]: {e}")
            await asyncio.sleep(5)
