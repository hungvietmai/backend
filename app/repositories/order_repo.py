from __future__ import annotations
from typing import Optional, List, Tuple
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.common.listing import paginate, safe_order_by, Col
from app.models.order import Order, OrderItem

ALLOWED_SORT: dict[str, Col] = {
    "id": Order.id,
    "order_number": Order.order_number,
    "status": Order.status,
    "total": Order.total_cents,
    "created_at": Order.created_at,
    "updated_at": Order.updated_at,
    "paid_at": Order.paid_at,
}
DEFAULT_SORT = ["-created_at"]


class OrderRepository:
    """Role-agnostic persistence for orders & items. No commits here."""
    def __init__(self, db: Session):
        self.db = db

    # ---------- Reads ----------
    def get(self, order_id: int) -> Optional[Order]:
        return self.db.get(Order, order_id)

    def get_by_number(self, order_number: str) -> Optional[Order]:
        stmt = select(Order).where(Order.order_number == order_number)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_paged(
        self,
        *,
        user_id: int | None,
        status: List[str] | None,
        created_from = None,
        created_to = None,
        min_total: int | None,
        max_total: int | None,
        sort: List[str],
        limit: int,
        offset: int,
    ) -> Tuple[List[Order], int]:
        stmt: Select[tuple[Order]] = select(Order).where(Order.deleted_at.is_(None))
        conds = []
        if user_id is not None: conds.append(Order.user_id == user_id)
        if status: conds.append(Order.status.in_(status))
        if created_from is not None: conds.append(Order.created_at >= created_from)
        if created_to   is not None: conds.append(Order.created_at <= created_to)
        if min_total    is not None: conds.append(Order.total_cents >= min_total)
        if max_total    is not None: conds.append(Order.total_cents <= max_total)

        if conds: stmt = stmt.where(and_(*conds))
        stmt = stmt.order_by(*safe_order_by(sort, ALLOWED_SORT, DEFAULT_SORT))
        return paginate(self.db, stmt, limit, offset)

    # ---------- Writes ----------
    def create(self, data: dict) -> Order:
        row = Order(**data)
        self.db.add(row)
        return row

    def save(self, row: Order) -> None:
        self.db.add(row)

    def add_item(self, order_id: int, data: dict) -> OrderItem:
        row = OrderItem(order_id=order_id, **data)
        self.db.add(row)
        return row

    def get_item(self, item_id: int) -> Optional[OrderItem]:
        return self.db.get(OrderItem, item_id)
