import os
import base64
import json
from datetime import datetime, timedelta
from typing import Optional, List

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from . import models

# ---------------------------------------------------------------------------
# AES-256-GCM at-rest encryption (FR-9.3). Key comes from env in real deploy;
# a fixed dev key is generated on first run and written to .aes_key for the
# prototype so restarts don't invalidate previously-encrypted rows.
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


_AES_KEY = os.getenv("IBVAP_AES_KEY_B64")
_AES_KEY = base64.b64decode(_AES_KEY) if _AES_KEY else _load_or_create_key()
_aesgcm = AESGCM(_AES_KEY)


def encrypt_field(plaintext: Optional[str]) -> Optional[str]:
    """AES-256-GCM encrypt a string field. Returns base64(nonce || ciphertext)."""
    if plaintext is None:
        return None
    nonce = os.urandom(12)
    ct = _aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("ascii")


def decrypt_field(blob: Optional[str]) -> Optional[str]:
    if blob is None:
        return None
    raw = base64.b64decode(blob)
    nonce, ct = raw[:12], raw[12:]
    return _aesgcm.decrypt(nonce, ct, None).decode("utf-8")


# ---------------------------------------------------------------------------
# Password hashing + JWT  (FR-9.2)
# ---------------------------------------------------------------------------
# pbkdf2_sha256 avoids the passlib/bcrypt backend version-detection breakage
# that's common in fresh environments; swap to bcrypt in production if you
# pin compatible passlib/bcrypt versions.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

SECRET_KEY = os.getenv("IBVAP_JWT_SECRET", "dev-only-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 10

ROLE_HIERARCHY = {"operator": 1, "supervisor": 2, "admin": 3}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(username: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exc
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exc
    return user


def get_current_user_optional(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """Returns authenticated user if token is valid, or a default operator instance if unauthenticated."""
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username:
                user = db.query(models.User).filter(models.User.username == username).first()
                if user:
                    return user
        except Exception:
            pass
    # Fallback to default operator for initial dashboard load
    return models.User(id=0, username="operator", role="operator")


def require_role(*allowed_roles: str, allow_guest_operator: bool = False):
    """Dependency factory for RBAC (FR-9.2). Roles are hierarchical:
    admin > supervisor > operator, so require_role('supervisor') also
    lets an admin through."""
    min_level = min(ROLE_HIERARCHY[r] for r in allowed_roles)

    def checker(user: models.User = Depends(get_current_user_optional if allow_guest_operator else get_current_user)) -> models.User:
        if ROLE_HIERARCHY.get(user.role, 0) < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role >= {allowed_roles}, you are '{user.role}'",
            )
        return user

    return checker


def check_lockout(user: models.User):
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining = int((user.locked_until - datetime.utcnow()).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked. Try again in {remaining}s.",
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
