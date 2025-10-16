from __future__ import annotations
from typing import Optional, Sequence
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.address import Address

class AddressRepository:
    def __init__(self, db: Session): self.db = db

    # --- reads ---
    def get(self, address_id: int) -> Optional[Address]:
        return self.db.get(Address, address_id)

    def list_for_user(self, user_id: int) -> Sequence[Address]:
        stmt = (
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        )
        return self.db.execute(stmt).scalars().all()

    def get_default_for_user(self, user_id: int) -> Optional[Address]:
        stmt = select(Address).where(Address.user_id == user_id, Address.is_default.is_(True))
        return self.db.execute(stmt).scalar_one_or_none()

    # --- writes (no commits) ---
    def create_for_user(self, user_id: int, data: dict) -> Address:
        row = Address(user_id=user_id, **data)
        self.db.add(row)
        return row

    def update(self, row: Address, data: dict) -> Address:
        for k, v in data.items(): setattr(row, k, v)
        self.db.add(row); return row

    def delete(self, row: Address) -> None:
        self.db.delete(row)

    def clear_default(self, user_id: int) -> None:
        # helpful before setting a new default (SQLite supports this fine)
        self.db.execute(
            update(Address).where(Address.user_id == user_id, Address.is_default.is_(True)).values(is_default=False)
        )
