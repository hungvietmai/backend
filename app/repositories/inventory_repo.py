from __future__ import annotations
from typing import Optional, Sequence, Tuple, List
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.common.listing import paginate, safe_order_by, Col
from app.models.inventory import InventoryMovement
from app.models.catalog import ProductVariant
from app.db.enums import InventoryMovementType

ALLOWED_SORT: dict[str, Col] = {
    "id": InventoryMovement.id,
    "created_at": InventoryMovement.created_at,
    "variant_id": InventoryMovement.variant_id,
    "order_id": InventoryMovement.order_id,
    "reason": InventoryMovement.reason,
    "qty_delta": InventoryMovement.qty_delta,
}
DEFAULT_SORT = ["-created_at"]

class InventoryRepository:
    def __init__(self, db: Session): self.db = db

    # --- variant reads/writes ---
    def load_variant(self, variant_id: int) -> Optional[ProductVariant]:
        return self.db.get(ProductVariant, variant_id)

    def change_stock(
        self,
        variant: ProductVariant,
        qty_delta: int,
        reason: InventoryMovementType,
        *,
        order_id: int | None,
        note: str | None = None,
    ) -> InventoryMovement:
        # persistence-level update + ledger record (no commit)
        variant.stock_qty = (variant.stock_qty or 0) + qty_delta
        self.db.add(variant)
        mov = InventoryMovement(
            variant_id=variant.id, order_id=order_id, qty_delta=qty_delta, reason=reason, note=note
        )
        self.db.add(mov)
        return mov

    # --- movement listing ---
    def list_movements_paged(
        self,
        *,
        variant_id: int | None,
        order_id: int | None,
        reason: InventoryMovementType | None,
        sort: List[str],
        limit: int,
        offset: int,
    ) -> Tuple[Sequence[InventoryMovement], int]:
        stmt: Select[tuple[InventoryMovement]] = select(InventoryMovement)
        conds = []
        if variant_id is not None: conds.append(InventoryMovement.variant_id == variant_id)
        if order_id is not None:   conds.append(InventoryMovement.order_id == order_id)
        if reason is not None:     conds.append(InventoryMovement.reason == reason)
        if conds: stmt = stmt.where(and_(*conds))
        stmt = stmt.order_by(*safe_order_by(sort, ALLOWED_SORT, DEFAULT_SORT))
        return paginate(self.db, stmt, limit, offset)
