import os
import base64
import json
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from . import models

# ---------------------------------------------------------------------------
# AES-256-GCM at-rest encryption & Key Rotation (FR-6.1, FR-6.5)
# ---------------------------------------------------------------------------
_KEY_PATH = os.path.join(os.path.dirname(__file__), "..", ".aes_key")


def _load_or_create_key() -> bytes:
    if os.path.exists(_KEY_PATH):
        with open(_KEY_PATH, "rb") as f:
            return f.read()
    key = AESGCM.generate_key(bit_length=256)
    with open(_KEY_PATH, "wb") as f:
        f.write(key)
    return key


_V1_AES_KEY = os.getenv("IBVAP_AES_KEY_B64")
_V1_AES_KEY = base64.b64decode(_V1_AES_KEY) if _V1_AES_KEY else _load_or_create_key()

_KEY_STORE: Dict[str, AESGCM] = {
    "v1": AESGCM(_V1_AES_KEY)
}
_ACTIVE_KEY_VERSION = "v1"


def rotate_key(new_version: str, key_bytes: Optional[bytes] = None) -> str:
    """Registers a new encryption key version for key rotation (FR-6.5)."""
    global _ACTIVE_KEY_VERSION
    if key_bytes is None:
        key_bytes = AESGCM.generate_key(bit_length=256)
    _KEY_STORE[new_version] = AESGCM(key_bytes)
    _ACTIVE_KEY_VERSION = new_version
    return new_version


def encrypt_field(plaintext: Optional[str], key_version: Optional[str] = None) -> Optional[str]:
    """AES-256-GCM encrypt a string field with versioned key prefix."""
    if plaintext is None:
        return None
    ver = key_version or _ACTIVE_KEY_VERSION
    cipher = _KEY_STORE.get(ver, _KEY_STORE["v1"])
    nonce = os.urandom(12)
    ct = cipher.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload_b64 = base64.b64encode(nonce + ct).decode("ascii")
    return f"{ver}:{payload_b64}"


def decrypt_field(blob: Optional[str]) -> Optional[str]:
    """Decrypts versioned or legacy AES-256-GCM ciphertext."""
    if blob is None:
        return None
    try:
        ver = "v1"
        data_b64 = blob
        if ":" in blob:
            parts = blob.split(":", 1)
            if parts[0] in _KEY_STORE:
                ver, data_b64 = parts[0], parts[1]

        cipher = _KEY_STORE.get(ver, _KEY_STORE["v1"])
        raw = base64.b64decode(data_b64)
        nonce, ct = raw[:12], raw[12:]
        return cipher.decrypt(nonce, ct, None).decode("utf-8")
    except Exception:
        return "[ENCRYPTED DATA - UNABLE TO DECRYPT]"


# ---------------------------------------------------------------------------
# Password hashing + JWT + Multi-Site RBAC (FR-1, FR-2, FR-6)
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

ENV = os.getenv("IBVAP_ENV", "development").lower()
SECRET_KEY = os.getenv("IBVAP_JWT_SECRET", "dev-only-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 10

ROLE_HIERARCHY = {"operator": 1, "supervisor": 2, "admin": 3, "service_account": 1}


def validate_production_config():
    """FR-6.1 / V4-06: Production startup fails if critical secrets or configs are unsafe."""
    if ENV == "production":
        if not SECRET_KEY or SECRET_KEY == "dev-only-change-me-in-production" or len(SECRET_KEY) < 24:
            raise RuntimeError("CRITICAL SECURITY ERROR: IBVAP_JWT_SECRET must be set to a strong secret in production (minimum 24 chars).")
        if not os.getenv("IBVAP_AES_KEY_B64"):
            raise RuntimeError("CRITICAL SECURITY ERROR: IBVAP_AES_KEY_B64 must be explicitly configured in production environment.")
        if os.getenv("IBVAP_C2_SECRET", "ibvap-tactical-c2-shared-key") == "ibvap-tactical-c2-shared-key":
            raise RuntimeError("CRITICAL SECURITY ERROR: IBVAP_C2_SECRET must be set to a unique production shared key.")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def resolve_user_site_ids(db: Session, user: models.User) -> List[str]:
    """FR-1.2 / V6-01: Dynamically resolves active site memberships for user from database."""
    if user.role == "admin":
        return ["*"]

    memberships = db.query(models.SiteMembership).filter(
        models.SiteMembership.user_id == user.id,
        models.SiteMembership.status == "active"
    ).all()

    if not memberships:
        return ["site-alpha"]  # Default base site if no explicit assignment
    return [m.site_id for m in memberships]


def create_access_token(username: str, role: str, site_ids: Optional[List[str]] = None) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    assigned_sites = site_ids if site_ids is not None else ["*"]
    payload = {
        "sub": username,
        "role": role,
        "site_ids": assigned_sites,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def validate_token(token: Optional[str]) -> Dict[str, Any]:
    """Validates JWT token and returns payload dict. Raises HTTPException 401 on failure."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims: subject missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def validate_site_access(payload: Dict[str, Any], site_id: str) -> bool:
    """FR-2.3 / V5-04: Enforces site-scoped authorization matrix."""
    allowed_sites = payload.get("site_ids", ["*"])
    if "*" in allowed_sites or site_id in allowed_sites:
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Access denied: Subject '{payload.get('sub')}' is not authorized for site '{site_id}'."
    )


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    payload = validate_token(token)
    username = payload.get("sub")
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(*allowed_roles: str, allow_guest_operator: bool = False):
    """Dependency factory for RBAC (FR-1 / FR-6). Roles are hierarchical."""
    min_level = min(ROLE_HIERARCHY.get(r, 1) for r in allowed_roles)

    def checker(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Dict[str, Any]:
        if not token:
            if allow_guest_operator and ENV == "test":
                return {"sub": "test_operator", "role": "operator", "site_ids": ["*"]}
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for this operation",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = validate_token(token)
        role = payload.get("role", "operator")

        if ROLE_HIERARCHY.get(role, 0) < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: requires role >= {allowed_roles}, your role is '{role}'",
            )
        return payload

    return checker


def authenticate_ws_token(token: Optional[str]) -> Dict[str, Any]:
    """FR-1.1: Validates token for WebSocket connections."""
    return validate_token(token)


def check_lockout(user: models.User):
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining = int((user.locked_until - datetime.utcnow()).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account temporarily locked due to multiple failed login attempts. Try again in {remaining}s.",
        )


def register_failed_attempt(user: models.User, db: Session):
    user.failed_attempts = (user.failed_attempts or 0) + 1
    if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
        user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
        user.failed_attempts = 0
    db.commit()


def reset_failed_attempts(user: models.User, db: Session):
    user.failed_attempts = 0
    user.locked_until = None
    db.commit()
