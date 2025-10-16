from __future__ import annotations
from typing import Optional, List, Tuple
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.common.listing import paginate, safe_order_by, ilike_any, Col
from app.models.auth import User

ALLOWED_SORT: dict[str, Col] = {
    "id": User.id,
    "email": User.email,
    "full_name": User.full_name,
    "role": User.role,
    "is_active": User.is_active,
    "created_at": User.created_at,
}
DEFAULT_SORT = ["-created_at"]


class UserRepository:
    """Role-agnostic user persistence (auth policies live in services). No commits here."""
    def __init__(self, db: Session):
        self.db = db

    # Reads
    def get(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_paged(
        self,
        *,
        q: str | None,
        role: str | None,
        is_active: bool | None,
        include_deleted: bool = False,
        sort: List[str],
        limit: int,
        offset: int,
    ) -> Tuple[List[User], int]:
        stmt: Select[tuple[User]] = select(User)
        conds = []
        if not include_deleted:
            conds.append(User.deleted_at.is_(None))
        if q:
            conds.append(ilike_any([User.email, User.full_name, User.phone], q))
        if role:
            conds.append(User.role == role)
        if is_active is not None:
            conds.append(User.is_active == is_active)

        if conds:
            stmt = stmt.where(and_(*conds))
        stmt = stmt.order_by(*safe_order_by(sort, ALLOWED_SORT, DEFAULT_SORT))
        return paginate(self.db, stmt, limit, offset)

    # Writes (no commit)
    def save(self, row: User) -> None:
        self.db.add(row)

    def create(self, data: dict) -> User:
        row = User(**data)
        self.db.add(row)
        return row

    def delete(self, row: User) -> None:
        self.db.delete(row)
