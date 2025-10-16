# app/services/auth_service.py
from __future__ import annotations
from typing import Optional
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_reset_token, decode_reset_token, password_fingerprint,
)
from app.exceptions import Conflict, Unauthorized, NotFound, BadRequest
from app.repositories.user_repo import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    # ---------- Register / Login ----------
    def register(self, email: str, password: str, full_name: Optional[str] = None):
        email = email.strip().lower()
        if len(password) < settings.PASSWORD_MIN_LEN:
            raise BadRequest(detail="Password too short")
        if self.users.get_by_email(email):
            raise Conflict(detail="Email already registered", errors={"email": ["taken"]})

        data = {
            "email": email,
            "hashed_password": hash_password(password),
            "full_name": full_name,
        }
        with self.db.begin():
            user = self.users.create(data)
        self.db.refresh(user)
        return user

    def login(self, email: str, password: str) -> str:
        email = email.strip().lower()
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise Unauthorized(detail="Incorrect email or password")
        if not user.is_active or user.deleted_at is not None:
            raise Unauthorized(detail="User disabled")
        return create_access_token(subject=str(user.id))

    # ---------- Forgot / Reset (stateless) ----------
    def forgot_password(self, email: str) -> dict:
        email = email.strip().lower()
        expires = settings.RESET_TOKEN_EXPIRE_MINUTES
        token: Optional[str] = None

        user = self.users.get_by_email(email)
        if user and user.is_active and user.deleted_at is None:
            fp = password_fingerprint(user.hashed_password)
            token = create_reset_token(user_id=user.id, pwd_fp=fp, minutes=expires)

        if settings.DEBUG or getattr(settings, "RETURN_RESET_TOKEN", False):
            return {"sent": True, "expires_in": expires, "token": token or ""}

        return {"sent": True, "expires_in": expires}

    def reset_password(self, token: str, new_password: str) -> None:
        if len(new_password) < settings.PASSWORD_MIN_LEN:
            raise BadRequest(detail="Password too short")

        try:
            payload = decode_reset_token(token)
        except JWTError:
            raise Unauthorized(detail="Invalid or expired reset token")

        sub = payload.get("sub")
        if not isinstance(sub, (str, int)) or (isinstance(sub, str) and not sub.isdigit()):
            raise Unauthorized(detail="Invalid or expired reset token")

        user = self.users.get(int(sub))
        if not user or not user.is_active or user.deleted_at is not None:
            raise Unauthorized(detail="Invalid or expired reset token")

        if password_fingerprint(user.hashed_password) != payload.get("fp"):
            raise Unauthorized(detail="Invalid or expired reset token")

        # Update via repo.save (no commit here)
        with self.db.begin():
            user.hashed_password = hash_password(new_password)
            self.users.save(user)

    # ---------- Change password (logged-in) ----------
    def change_password(self, user_id: int, current_password: str, new_password: str) -> None:
        user = self.users.get(user_id)
        if not user or user.deleted_at is not None:
            raise NotFound(detail="User not found")
        if not user.is_active:
            raise Unauthorized(detail="User disabled")
        if not verify_password(current_password, user.hashed_password):
            raise Unauthorized(detail="Current password incorrect")
        if len(new_password) < settings.PASSWORD_MIN_LEN:
            raise BadRequest(detail="Password too short")

        with self.db.begin():
            user.hashed_password = hash_password(new_password)
            self.users.save(user)
