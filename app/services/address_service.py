# app/services/address_service.py
from __future__ import annotations
from sqlalchemy.orm import Session

from app.repositories.address_repo import AddressRepository
from app.exceptions import NotFound


class AddressService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AddressRepository(db)

    # -------- Reads --------
    def list_my(self, user_id: int):
        return self.repo.list_for_user(user_id)

    def _owned(self, user_id: int, address_id: int):
        row = self.repo.get(address_id)
        if not row or row.user_id != user_id:
            raise NotFound("Address not found")
        return row

    # -------- Writes --------
    def create(self, user_id: int, data: dict):
        # First address becomes default automatically
        if not self.repo.list_for_user(user_id):
            data = {**data, "is_default": True}

        # If caller wants this new one to be default → clear others first
        if data.get("is_default"):
            self.repo.clear_default(user_id)
        row = self.repo.create_for_user(user_id, data)

        self.db.commit()
        self.db.refresh(row)
        return row

    def update(self, user_id: int, address_id: int, data: dict):
        row = self._owned(user_id, address_id)

        # Only treat True specially (switch default). We ignore explicit False
        # to avoid ending up with zero defaults. Use make_default() to switch.
        if data.get("is_default") is True:
            self.repo.clear_default(user_id)
        row = self.repo.update(row, data)

        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, user_id: int, address_id: int) -> None:
        row = self._owned(user_id, address_id)
        was_default = bool(row.is_default)

        self.repo.delete(row)
        # If we removed the default, ensure another becomes default (if any remain)
        if was_default:
            remaining = self.repo.list_for_user(user_id)
            if remaining:
                self.repo.update(remaining[0], {"is_default": True})

        self.db.commit()

    def make_default(self, user_id: int, address_id: int):
        row = self._owned(user_id, address_id)
        self.repo.clear_default(user_id)
        row = self.repo.update(row, {"is_default": True})
        self.db.commit()
        self.db.refresh(row)
        return row
