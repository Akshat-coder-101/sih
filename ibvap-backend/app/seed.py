"""
Seeds the DB with realistic starting data, multi-site tenancy, virtual fence rules, and users.
All seeded alerts are tagged with `provenance='simulation'` per PRD v2.0 FR-4.8
so operators can filter real detector alerts from simulation benchmarks.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from . import models
from .security import hash_password, encrypt_field
from .ledger import append_to_ledger

INITIAL_SITES = [
    dict(id="site-alpha", name="Sector North BOP Alpha", region="Northern Frontier", timezone="UTC", retention_days=90),
    dict(id="site-bravo", name="Sector North BOP Bravo", region="Northern Frontier", timezone="UTC", retention_days=90),
]

INITIAL_CAMS = [
    dict(id="cam-1", site_id="site-alpha", name="CAM-01 · North Perimeter", location="BOP Alpha — North Fence Line",
         online=True, priority="High", fps=9, night=False, scene="fence",
         geo="29.5481°N 74.8763°E", anchor={"left": 44, "top": 46, "w": 9, "h": 26},
         rtsp_url="rtsp://cam-1.bop.local:554/stream1"),
    dict(id="cam-2", site_id="site-alpha", name="CAM-02 · Check Post Gate", location="BOP Alpha — Gate Road",
         online=True, priority="Medium", fps=8, night=False, scene="gate",
         geo="29.5502°N 74.8791°E", anchor={"left": 41, "top": 52, "w": 20, "h": 24},
         rtsp_url="rtsp://cam-2.bop.local:554/stream2"),
    dict(id="cam-3", site_id="site-bravo", name="CAM-03 · Border Road", location="BOP Bravo — Approach Road",
         online=True, priority="High", fps=9, night=True, scene="night",
         geo="29.6104°N 74.9038°E", anchor={"left": 47, "top": 50, "w": 18, "h": 22},
         rtsp_url="rtsp://cam-3.bop.local:554/stream1"),
    dict(id="cam-4", site_id="site-bravo", name="CAM-04 · East Watchtower", location="BOP Bravo — East Ridge",
         online=False, priority="Medium", fps=0, night=False, scene="fence",
         geo="29.6140°N 74.9102°E", anchor={"left": 44, "top": 46, "w": 9, "h": 26},
         rtsp_url="rtsp://cam-4.bop.local:554/stream2"),
]

INITIAL_FENCE_RULES = [
    dict(id="rule-cam1-01", site_id="site-alpha", camera_id="cam-1", name="North Fence Tripwire",
         rule_type="tripwire", direction="bidirectional",
         coordinates=[[10.0, 70.0], [90.0, 70.0]],
         target_classes=["person", "car", "truck", "motorcycle"],
         severity="high", enabled=True, cooldown_seconds=10),
    dict(id="rule-cam2-01", site_id="site-alpha", camera_id="cam-2", name="Gate Entry Zone",
         rule_type="polygon_zone", direction="entry",
         coordinates=[[20.0, 40.0], [80.0, 40.0], [85.0, 90.0], [15.0, 90.0]],
         target_classes=["person", "car", "truck"],
         severity="high", enabled=True, cooldown_seconds=15),
    dict(id="rule-cam3-01", site_id="site-bravo", camera_id="cam-3", name="Road Perimeter Tripwire",
         rule_type="tripwire", direction="bidirectional",
         coordinates=[[5.0, 60.0], [95.0, 60.0]],
         target_classes=["person", "car", "truck", "motorcycle"],
         severity="med", enabled=True, cooldown_seconds=15),
]

TYPE_SEV = {
    "intrusion": "high", "watchlist": "high", "anpr": "med",
    "loiter": "med", "night": "low", "weapon": "high",
}

INITIAL_ALERTS = [
    ("intrusion", "cam-1", 3, "Person crossed north fence line", False, "open"),
    ("watchlist", "cam-2", 9, "Match: Watchlist ID WL-014 (Person of Interest)", False, "open"),
    ("anpr", "cam-2", 14, "Plate PB-11-AK-4471 — flagged vehicle list", False, "open"),
    ("loiter", "cam-3", 21, "Individual stationary 4m+ near border road", True, "acknowledged"),
    ("night", "cam-3", 27, "Movement detected in low-light conditions", True, "resolved"),
    ("intrusion", "cam-3", 35, "Vehicle crossed approach-road boundary", True, "resolved"),
    ("watchlist", "cam-1", 48, "Match: Watchlist ID WL-009 (Person of Interest)", True, "resolved"),
    ("anpr", "cam-3", 55, "Plate RJ-06-CT-1183 — flagged vehicle list", True, "resolved"),
    ("loiter", "cam-2", 72, "Individual stationary 5m+ near gate", True, "resolved"),
    ("night", "cam-1", 95, "Movement detected in low-light conditions", True, "resolved"),
    ("intrusion", "cam-2", 130, "Person crossed gate-road boundary", True, "resolved"),
    ("anpr", "cam-1", 160, "Plate HR-26-BQ-7742 — flagged vehicle list", True, "resolved"),
]

DEMO_USERS = [
    ("admin", "admin123", "admin"),
    ("supervisor", "supervisor123", "supervisor"),
    ("operator", "operator123", "operator"),
]


def run_seed(db: Session):
    if db.query(models.Site).count() == 0:
        for s in INITIAL_SITES:
            db.add(models.Site(**s))
        db.commit()

    if db.query(models.Camera).count() == 0:
        for c in INITIAL_CAMS:
            db.add(models.Camera(**c))
        db.commit()

    if db.query(models.FenceRule).count() == 0:
        for r in INITIAL_FENCE_RULES:
            db.add(models.FenceRule(**r))
        db.commit()

    if db.query(models.Alert).count() == 0:
        seq = 1
        cams_by_id = {c["id"]: c for c in INITIAL_CAMS}
        for type_, cam_id, mins_ago, detail, reviewed, state in INITIAL_ALERTS:
            cam = cams_by_id[cam_id]
            alert_ts = datetime.utcnow() - timedelta(minutes=mins_ago)
            alert = models.Alert(
                id=f"EVT-{seq:04d}",
                site_id=cam.get("site_id", "site-alpha"),
                type=type_,
                sev=TYPE_SEV[type_],
                cam_id=cam_id,
                cam_name=cam["name"],
                location=cam["location"],
                confidence=80 + (seq * 3) % 20,
                track_id=f"#{100 + seq * 7}",
                detail_enc=encrypt_field(detail),
                reviewed=reviewed,
                state=state,
                provenance="simulation",
                model_version="8.2.0",
                rule_id=f"rule-{cam_id}-01",
                rule_version="1.0",
                source_frame_time=alert_ts,
                ts=alert_ts,
                snapshot_enc=None,
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
            append_to_ledger(db, alert)
            seq += 1

    if db.query(models.User).count() == 0:
        for username, password, role in DEMO_USERS:
            db.add(models.User(
                username=username,
                hashed_password=hash_password(password),
                role=role,
            ))
        db.commit()

    if db.query(models.GovernanceApproval).count() == 0:
        db.add(models.GovernanceApproval(
            id="GOV-FACE-SITE-ALPHA",
            site_id="site-alpha",
            capability="face_recognition",
            legal_approval_ref="LEGAL-SEC-2026-089A",
            approved_by="HQ Legal Director",
            restricted_mode=False
        ))
        db.add(models.GovernanceApproval(
            id="GOV-ANPR-SITE-ALPHA",
            site_id="site-alpha",
            capability="anpr",
            legal_approval_ref="LEGAL-MHA-2026-4421",
            approved_by="HQ Legal Director",
            restricted_mode=False
        ))
        db.commit()
