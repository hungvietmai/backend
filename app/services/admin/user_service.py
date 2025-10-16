# app/services/admin/user_service.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List, cast

from sqlalchemy.orm import Session

from app.repositories.user_repo import UserRepository
from app.schemas.page import Page
from app.schemas.user import UserOut
from app.db.enums import UserRoleEnum
from app.exceptions import NotFound


class AdminUserService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    # ---------- Read / List ----------
    def list_page(
        self,
        *,
        q: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        include_deleted: bool = True,            # admin usually sees deleted too
        sort: List[str] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Page[UserOut]:
        items, total = self.repo.list_paged(
            q=q,
            role=role,
            is_active=is_active,
            include_deleted=include_deleted,
            sort=sort or ["-created_at"],
            limit=limit,
            offset=offset,
        )
        dto = [UserOut.model_validate(u, from_attributes=True) for u in items]
        return Page[UserOut].from_parts(dto, total, limit, offset)

    # ---------- Mutations ----------
    def _get_or_404(self, user_id: int):
        u = self.repo.get(user_id)
        if not u:
            raise NotFound("User not found")
        return u

    def set_role(self, user_id: int, role: UserRoleEnum):
        u = self._get_or_404(user_id)
        with self.db.begin():
            u.role = role
            self.repo.save(u)
        self.db.refresh(u)
        return u

    def set_active(self, user_id: int, active: bool):
        u = self._get_or_404(user_id)
        with self.db.begin():
            u.is_active = active
            self.repo.save(u)
        self.db.refresh(u)
        return u

    def soft_delete(self, user_id: int):
        u = self._get_or_404(user_id)
        now = datetime.now(timezone.utc)
        with self.db.begin():
            u.deleted_at = cast("datetime | None", now)   # keep type checker happy
            self.repo.save(u)
        # optional: don’t refresh; returning a simple payload is fine
        return {"ok": True}

    def restore(self, user_id: int):
        u = self._get_or_404(user_id)
        with self.db.begin():
            u.deleted_at = cast("datetime | None", None)
            self.repo.save(u)
        self.db.refresh(u)
        return u
