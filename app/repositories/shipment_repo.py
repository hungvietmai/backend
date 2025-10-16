from __future__ import annotations
from typing import Optional, Sequence, Tuple, List
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.common.listing import paginate, safe_order_by, Col
from app.models.shipment import Shipment

ALLOWED_SORT: dict[str, Col] = {
    "id": Shipment.id,
    "order_id": Shipment.order_id,
    "status": Shipment.status,
    "created_at": Shipment.created_at,
    "shipped_at": Shipment.shipped_at,
    "delivered_at": Shipment.delivered_at,
}
DEFAULT_SORT = ["-created_at"]

class ShipmentRepository:
    def __init__(self, db: Session): self.db = db

    # --- reads ---
    def get(self, shipment_id: int) -> Optional[Shipment]: return self.db.get(Shipment, shipment_id)

    def get_by_order(self, order_id: int) -> Optional[Shipment]:
        stmt = select(Shipment).where(Shipment.order_id == order_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_paged(
        self,
        *,
        order_id: int | None,
        status: list[str] | None,
        sort: List[str],
        limit: int,
        offset: int,
    ) -> Tuple[Sequence[Shipment], int]:
        stmt: Select[tuple[Shipment]] = select(Shipment)
        conds = []
        if order_id is not None: conds.append(Shipment.order_id == order_id)
        if status: conds.append(Shipment.status.in_(status))
        if conds: stmt = stmt.where(and_(*conds))
        stmt = stmt.order_by(*safe_order_by(sort, ALLOWED_SORT, DEFAULT_SORT))
        return paginate(self.db, stmt, limit, offset)

    # --- writes (no commits) ---
    def create(self, order_id: int, data: dict) -> Shipment:
        row = Shipment(order_id=order_id, **data); self.db.add(row); return row

    def update(self, row: Shipment, data: dict) -> Shipment:
        for k, v in data.items(): setattr(row, k, v)
        self.db.add(row); return row
