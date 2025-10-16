from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Dict
import hashlib
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing (sha256)
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# JWT helpers
def create_access_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    to_encode: dict[str, Any] = {"sub": str(subject)}
    if extra_claims:
        to_encode.update(extra_claims)
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.JWT_SECRET)

def decode_token(token: str) -> dict[str, Any]:
    # Raise on invalid/expired
    return jwt.decode(token, settings.JWT_SECRET)

def password_fingerprint(hashed_password: str) -> str:
    """Stable fingerprint; changes whenever user changes their password."""
    return hashlib.sha256(hashed_password.encode("utf-8")).hexdigest()

def create_reset_token(user_id: int, pwd_fp: str, minutes: int) -> str:
    """Short-lived, signed JWT specifically for password reset."""
    claims = {"pr": "pwd_reset", "fp": pwd_fp}
    return create_access_token(
        subject=user_id,
        expires_delta=timedelta(minutes=minutes),
        extra_claims=claims,
    )

def decode_reset_token(token: str) -> Dict[str, Any]:
    """Verify signature + purpose; raise JWTError if anything is off."""
    payload = decode_token(token)  # verifies signature & exp
    if payload.get("pr") != "pwd_reset":
        raise JWTError("Invalid token purpose")
    if "fp" not in payload:
        raise JWTError("Missing fingerprint")
    return payload