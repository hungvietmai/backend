from __future__ import annotations
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.sql import Select

from app.repositories.returns_repo import ReturnsRepository
from app.repositories.order_repo import OrderRepository
from app.schemas.page import Page
from app.schemas.returns import ReturnOut
from app.db.enums import OrderStatusEnum
from app.exceptions import NotFound, BadRequest

from app.models.order import Order       # for the join in list_my_page
from app.models.returns import ReturnRequest, ReturnItem
from app.common.listing import paginate, safe_order_by, Col


ALLOWED_SORT: dict[str, Col] = {
    "id": ReturnRequest.id,
    "order_id": ReturnRequest.order_id,
    "status": ReturnRequest.status,
    "created_at": ReturnRequest.created_at,
}
DEFAULT_SORT = ["-created_at"]


class ReturnsService:
    def __init__(self, db: Session):
        self.db = db
        self.returns = ReturnsRepository(db)
        self.orders = OrderRepository(db)

    # -------- list & detail (user-scoped) --------
    def list_my_page(
        self,
        user_id: int,
        *,
        status: Optional[List[str]] = None,
        sort: List[str] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Page[ReturnOut]:
        # The repo doesn't provide a user-scoped listing; do a small join here.
        stmt: Select[tuple[ReturnRequest]] = (
            select(ReturnRequest)
            .join(Order, Order.id == ReturnRequest.order_id)
            .where(Order.user_id == user_id)
        )
        if status:
            stmt = stmt.where(ReturnRequest.status.in_(status))
        stmt = stmt.order_by(*safe_order_by(sort or DEFAULT_SORT, ALLOWED_SORT, DEFAULT_SORT))

        items, total = paginate(self.db, stmt, limit, offset)
        dto = [ReturnOut.model_validate(r, from_attributes=True) for r in items]
        return Page[ReturnOut].from_parts(dto, total, limit, offset)

    def get_for_user(self, user_id: int, return_id: int):
        r = self.returns.get(return_id)
        if not r or not r.order or r.order.user_id != user_id:
            raise NotFound("Return not found")
        return r

    # -------- create & modify --------
    def create(self, user_id: int, order_id: int, reason: str | None):
        o = self.orders.get(order_id)
        if not o or o.user_id != user_id:
            raise NotFound("Order not found")
        if o.status not in {OrderStatusEnum.paid, OrderStatusEnum.fulfilled}:
            raise BadRequest("Order not eligible for return")

        with self.db.begin():
            r = self.returns.create_request(order_id, reason=reason)
        self.db.refresh(r)
        return r

    def add_item(self, user_id: int, return_id: int, order_item_id: int, qty: int):
        if qty <= 0:
            raise BadRequest("qty must be > 0")

        r = self.get_for_user(user_id, return_id)  # checks ownership

        oi = self.orders.get_item(order_item_id)
        if not oi or oi.order_id != r.order_id:
            raise NotFound("Order item not found")
        if qty > oi.qty:
            raise BadRequest("qty exceeds purchased amount")

        with self.db.begin():
            row = self.returns.add_item(return_id, order_item_id=order_item_id, qty=qty)
        self.db.refresh(row)
        return row

    def remove_item(self, user_id: int, return_item_id: int) -> None:
        # Your repo doesn't expose delete/get for ReturnItem; do minimal direct access here.
        ri = self.db.get(ReturnItem, return_item_id)
        if not ri:
            return
        rr = self.returns.get(ri.return_id)
        if not rr or not rr.order or rr.order.user_id != user_id:
            raise NotFound("Return item not found")
        with self.db.begin():
            self.db.delete(ri)
