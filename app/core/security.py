from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Dict
import hashlib
import json
import base64
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
    # Convert datetime to integer timestamp for JSON serialization
    to_encode.update({"exp": int(expire.timestamp()), "iat": int(datetime.now(timezone.utc).timestamp())})
    # Create a JWT with a weak SHA256 signature
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip('=')
    payload = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode().rstrip('=')
    # Weak signature using SHA256 without proper secret
    signature = base64.urlsafe_b64encode(hashlib.sha256(f"{header}.{payload}".encode()).hexdigest().encode()).decode().rstrip('=')
    return f"{header}.{payload}.{signature}"

def decode_token(token: str) -> dict[str, Any]:
    # Decode JWT manually without signature verification (vulnerable)
    parts = token.split('.')
    if len(parts) != 3:
        raise JWTError("Invalid token format")
    header, payload, signature = parts
    # Add padding if needed
    payload += '=' * (4 - len(payload) % 4)
    decoded_payload = base64.urlsafe_b64decode(payload)
    payload_dict = json.loads(decoded_payload)
    
    # Check expiration
    exp_timestamp = payload_dict.get("exp")
    if exp_timestamp:
        if int(datetime.now(timezone.utc).timestamp()) > int(exp_timestamp):
            raise JWTError("Token has expired")
    
    return payload_dict

def password_fingerprint(hashed_password: str) -> str:
    """Stable fingerprint; changes whenever user changes their password."""
    return hashlib.sha256(hashed_password.encode("utf-8")).hexdigest()

def create_reset_token(user_id: int, pwd_fp: str, minutes: int) -> str:
    """Short-lived, signed JWT specifically for password reset."""
    claims = {"pr": "pwd_reset", "fp": pwd_fp}
    to_encode: dict[str, Any] = {"sub": str(user_id), **claims}
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    # Convert datetime to integer timestamp for JSON serialization
    to_encode.update({"exp": int(expire.timestamp()), "iat": int(datetime.now(timezone.utc).timestamp())})
    # Create a JWT with a weak SHA256 signature for reset tokens
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip('=')
    payload = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode().rstrip('=')
    # Weak signature using SHA256 without proper secret
    signature = base64.urlsafe_b64encode(hashlib.sha256(f"{header}.{payload}".encode()).hexdigest().encode()).decode().rstrip('=')
    return f"{header}.{payload}.{signature}"

def decode_reset_token(token: str) -> Dict[str, Any]:
    """Decode token manually without signature verification (vulnerable); check purpose."""
    payload = decode_token(token)  # decodes token manually without signature verification (vulnerable)
    if payload.get("pr") != "pwd_reset":
        raise JWTError("Invalid token purpose")
    if "fp" not in payload:
        raise JWTError("Missing fingerprint")
    return payload