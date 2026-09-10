from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Camera(Base):
    """Mirrors the `Camera` interface in the frontend's types/index.ts"""
    __tablename__ = "cameras"

    id = Column(String, primary_key=True)          # e.g. 'cam-1'
    name = Column(String, nullable=False)           # 'CAM-01 · North Perimeter'
    location = Column(String, nullable=False)
    online = Column(Boolean, default=True)
    priority = Column(String, default="Medium")     # High | Medium | Low
    fps = Column(Integer, default=0)
    night = Column(Boolean, default=False)
    scene = Column(String, default="fence")          # fence | gate | night (SVG fallback key)
    geo = Column(String, default="")
    anchor = Column(JSON, default=lambda: {"left": 44, "top": 46, "w": 9, "h": 26})
    rtsp_url = Column(String, nullable=True)

    alerts = relationship("Alert", back_populates="camera")


class Alert(Base):
    """Mirrors the `Alert` interface in the frontend's types/index.ts.
    NOTE: `detail` and `snapshot` are stored AES-256-GCM encrypted at rest
    (see security.py) — the plaintext versions never touch disk."""
    __tablename__ = "alerts"

    id = Column(String, primary_key=True)            # 'EVT-0001'
    type = Column(String, nullable=False)             # intrusion|watchlist|anpr|loiter|night|weapon
    sev = Column(String, nullable=False)               # high|med|low
    cam_id = Column(String, ForeignKey("cameras.id"))
    cam_name = Column(String)
    location = Column(String)
    confidence = Column(Integer)
    track_id = Column(String)
    detail_enc = Column(Text)          # AES-256-GCM ciphertext (base64), decrypted on read
    reviewed = Column(Boolean, default=False)
    ts = Column(DateTime, default=datetime.utcnow)
    snapshot_enc = Column(Text, nullable=True)  # AES-256-GCM ciphertext of the JPEG data-URL

    camera = relationship("Camera", back_populates="alerts")
    ledger_record = relationship("LedgerRecord", back_populates="alert", uselist=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # operator | supervisor | admin
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)


class AuditLog(Base):
    """Distinct from the AI event log (Alert table) per FR-9.4:
    records human actions — login, export, config change — not AI detections."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    action = Column(String, nullable=False)   # 'login', 'export_csv', 'toggle_camera', 'mark_reviewed', ...
    detail = Column(String, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow)


class LedgerRecord(Base):
    """SHA-256 append-only hash-chain over Alert records (FR-10).
    record_hash = SHA256(canonical_alert_json + prev_hash)
    Tampering with the underlying Alert row is detected because recomputing
    record_hash from the CURRENT alert data will no longer match what's stored
    here, breaking the chain from that point forward."""
    __tablename__ = "ledger_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    seq = Column(Integer, unique=True, nullable=False)   # chain position, 0-indexed
    alert_id = Column(String, ForeignKey("alerts.id"), unique=True)
    prev_hash = Column(String, nullable=False)
    record_hash = Column(String, nullable=False)
    ts = Column(DateTime, default=datetime.utcnow)

    alert = relationship("Alert", back_populates="ledger_record")
