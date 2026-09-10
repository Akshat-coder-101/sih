from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


def to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


# ---------- Camera ----------
class Anchor(CamelModel):
    left: float
    top: float
    w: float
    h: float


class CameraOut(CamelModel):
    id: str
    name: str
    location: str
    online: bool
    priority: str
    fps: int
    night: bool
    scene: str
    geo: str
    anchor: Anchor
    rtsp_url: Optional[str] = None


class CameraCreate(CamelModel):
    id: str
    name: str
    location: str
    online: bool = True
    priority: str = "Medium"
    fps: int = 0
    night: bool = False
    scene: str = "fence"
    geo: str = ""
    anchor: Anchor = Anchor(left=44, top=46, w=9, h=26)
    rtsp_url: Optional[str] = None


# ---------- Alert ----------
class AlertOut(CamelModel):
    id: str
    type: str
    sev: str
    cam_id: str
    cam_name: str
    location: str
    confidence: int
    track_id: str
    detail: str
    reviewed: bool
    ts: datetime
    snapshot: Optional[str] = None


class AlertCreate(CamelModel):
    type: str
    cam_id: str
    detail: str
    confidence: Optional[int] = None
    track_id: Optional[str] = None
    snapshot: Optional[str] = None
    sev: Optional[str] = None  # falls back to TYPE_META default if omitted


# ---------- Auth ----------
class LoginRequest(CamelModel):
    username: str
    password: str


class TokenResponse(CamelModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


# ---------- Ledger ----------
class LedgerVerifyResult(CamelModel):
    intact: bool
    checked_records: int
    broken_at_seq: Optional[int] = None
    broken_alert_id: Optional[str] = None
    message: str


# ---------- Audit ----------
class AuditLogOut(CamelModel):
    id: int
    username: str
    action: str
    detail: Optional[str] = None
    ts: datetime
