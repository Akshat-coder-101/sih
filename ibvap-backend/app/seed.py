"""
Seeds the DB with the same starting data the frontend used to fabricate
client-side (INITIAL_CAMS / INITIAL_ALERTS in AppContext.tsx), so swapping
the frontend over to this backend produces an identical first-load demo.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from . import models
from .security import hash_password, encrypt_field
from .ledger import append_to_ledger

INITIAL_CAMS = [
    dict(id="cam-1", name="CAM-01 · North Perimeter", location="BOP Alpha — North Fence Line",
         online=True, priority="High", fps=9, night=False, scene="fence",
         geo="29.5481°N 74.8763°E", anchor={"left": 44, "top": 46, "w": 9, "h": 26},
         rtsp_url="rtsp://cam-1.bop.local:554/stream1"),
    dict(id="cam-2", name="CAM-02 · Check Post Gate", location="BOP Alpha — Gate Road",
         online=True, priority="Medium", fps=8, night=False, scene="gate",
         geo="29.5502°N 74.8791°E", anchor={"left": 41, "top": 52, "w": 20, "h": 24},
         rtsp_url="rtsp://cam-2.bop.local:554/stream2"),
    dict(id="cam-3", name="CAM-03 · Border Road", location="BOP Bravo — Approach Road",
         online=True, priority="High", fps=9, night=True, scene="night",
         geo="29.6104°N 74.9038°E", anchor={"left": 47, "top": 50, "w": 18, "h": 22},
         rtsp_url="rtsp://cam-3.bop.local:554/stream1"),
    dict(id="cam-4", name="CAM-04 · East Watchtower", location="BOP Bravo — East Ridge",
         online=False, priority="Medium", fps=0, night=False, scene="fence",
         geo="29.6140°N 74.9102°E", anchor={"left": 44, "top": 46, "w": 9, "h": 26},
         rtsp_url="rtsp://cam-4.bop.local:554/stream2"),
]

TYPE_SEV = {
    "intrusion": "high", "watchlist": "high", "anpr": "med",
    "loiter": "med", "night": "low", "weapon": "high",
}

INITIAL_ALERTS = [
    ("intrusion", "cam-1", 3, "Person crossed north fence line", False),
    ("watchlist", "cam-2", 9, "Match: Watchlist ID WL-014 (Person of Interest)", False),
    ("anpr", "cam-2", 14, "Plate PB-11-AK-4471 — flagged vehicle list", False),
    ("loiter", "cam-3", 21, "Individual stationary 4m+ near border road", True),
    ("night", "cam-3", 27, "Movement detected in low-light conditions", True),
    ("intrusion", "cam-3", 35, "Vehicle crossed approach-road boundary", True),
    ("watchlist", "cam-1", 48, "Match: Watchlist ID WL-009 (Person of Interest)", True),
    ("anpr", "cam-3", 55, "Plate RJ-06-CT-1183 — flagged vehicle list", True),
    ("loiter", "cam-2", 72, "Individual stationary 5m+ near gate", True),
    ("night", "cam-1", 95, "Movement detected in low-light conditions", True),
    ("intrusion", "cam-2", 130, "Person crossed gate-road boundary", True),
    ("anpr", "cam-1", 160, "Plate HR-26-BQ-7742 — flagged vehicle list", True),
]

DEMO_USERS = [
    ("admin", "admin123", "admin"),
    ("supervisor", "supervisor123", "supervisor"),
    ("operator", "operator123", "operator"),
]


def run_seed(db: Session):
    if db.query(models.Camera).count() == 0:
        for c in INITIAL_CAMS:
            db.add(models.Camera(**{
                "id": c["id"], "name": c["name"], "location": c["location"],
                "online": c["online"], "priority": c["priority"], "fps": c["fps"],
                "night": c["night"], "scene": c["scene"], "geo": c["geo"],
                "anchor": c["anchor"], "rtsp_url": c["rtsp_url"],
            }))
        db.commit()

    if db.query(models.Alert).count() == 0:
        seq = 1
        cams_by_id = {c["id"]: c for c in INITIAL_CAMS}
        for type_, cam_id, mins_ago, detail, reviewed in INITIAL_ALERTS:
            cam = cams_by_id[cam_id]
            alert = models.Alert(
                id=f"EVT-{seq:04d}",
                type=type_,
                sev=TYPE_SEV[type_],
                cam_id=cam_id,
                cam_name=cam["name"],
                location=cam["location"],
                confidence=80 + (seq * 3) % 20,
                track_id=f"#{100 + seq * 7}",
                detail_enc=encrypt_field(detail),
                reviewed=reviewed,
                ts=datetime.utcnow() - timedelta(minutes=mins_ago),
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
        print("Seeded demo accounts (CHANGE THESE BEFORE ANY REAL DEPLOYMENT):")
        for username, password, role in DEMO_USERS:
            print(f"  {role:12s} -> {username} / {password}")
