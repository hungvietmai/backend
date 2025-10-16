from __future__ import annotations
from typing import Optional, Sequence, Tuple, List
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.common.listing import paginate, safe_order_by, Col
from app.models.returns import ReturnRequest, ReturnItem

ALLOWED_SORT: dict[str, Col] = {
    "id": ReturnRequest.id,
    "order_id": ReturnRequest.order_id,
    "status": ReturnRequest.status,
    "created_at": ReturnRequest.created_at,
}
DEFAULT_SORT = ["-created_at"]

class ReturnsRepository:
    def __init__(self, db: Session): self.db = db

    # --- reads ---
    def get(self, return_id: int) -> Optional[ReturnRequest]:
        return self.db.get(ReturnRequest, return_id)

    def list_paged(
        self,
        *,
        order_id: int | None,
        status: list[str] | None,
        sort: List[str],
        limit: int,
        offset: int,
    ) -> Tuple[Sequence[ReturnRequest], int]:
        stmt: Select[tuple[ReturnRequest]] = select(ReturnRequest)
        conds = []
        if order_id is not None: conds.append(ReturnRequest.order_id == order_id)
        if status: conds.append(ReturnRequest.status.in_(status))
        if conds: stmt = stmt.where(and_(*conds))
        stmt = stmt.order_by(*safe_order_by(sort, ALLOWED_SORT, DEFAULT_SORT))
        return paginate(self.db, stmt, limit, offset)

    def list_items(self, return_id: int) -> Sequence[ReturnItem]:
        stmt = select(ReturnItem).where(ReturnItem.return_id == return_id).order_by(ReturnItem.id.asc())
        return self.db.execute(stmt).scalars().all()

    # --- writes (no commits) ---
    def create_request(self, order_id: int, *, reason: str | None) -> ReturnRequest:
        row = ReturnRequest(order_id=order_id, reason=reason)
        self.db.add(row); return row

    def add_item(self, return_id: int, *, order_item_id: int, qty: int) -> ReturnItem:
        row = ReturnItem(return_id=return_id, order_item_id=order_item_id, qty=qty)
        self.db.add(row); return row

    def save(self, row: ReturnRequest) -> None:
        self.db.add(row)
