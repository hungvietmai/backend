# app/services/admin/inventory_service.py
from __future__ import annotations
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.repositories.inventory_repo import InventoryRepository
from app.db.enums import InventoryMovementType
from app.models.inventory import InventoryMovement
from app.exceptions import NotFound, BadRequest

class AdminInventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.inv = InventoryRepository(db)

    def list_movements_page(
        self,
        *,
        variant_id: int | None = None,
        order_id: int | None = None,
        reason: InventoryMovementType | None = None,
        sort: List[str] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[InventoryMovement], int, int, int]:
        items_seq, total = self.inv.list_movements_paged(
            variant_id=variant_id,
            order_id=order_id,
            reason=reason,
            sort=sort or ["-created_at"],
            limit=limit,
            offset=offset,
        )
        return list(items_seq), total, limit, offset

    def manual_adjust(self, *, variant_id: int, qty_delta: int, note: str | None = None) -> InventoryMovement:
        if qty_delta == 0:
            raise BadRequest("qty_delta cannot be 0")
        v = self.inv.load_variant(variant_id)
        if not v:
            raise NotFound("Variant not found")
        with self.db.begin():
            mov = self.inv.change_stock(
                v,
                qty_delta=qty_delta,
                reason=InventoryMovementType.manual_adjust,
                order_id=None,
                note=note,
            )
        self.db.refresh(mov)
        return mov
