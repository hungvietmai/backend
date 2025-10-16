# app/services/admin/returns_service.py
from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.repositories.returns_repo import ReturnsRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.payment_repo import PaymentRepository
from app.repositories.inventory_repo import InventoryRepository

from app.models.returns import ReturnRequest
from app.db.enums import (
    ReturnStatusEnum,
    InventoryMovementType,
    PaymentStatusEnum,
    PaymentMethodEnum,
    OrderStatusEnum,
)
from app.exceptions import NotFound, BadRequest


class AdminReturnsService:
    def __init__(self, db: Session):
        self.db = db
        self.returns = ReturnsRepository(db)
        self.orders = OrderRepository(db)
        self.payments = PaymentRepository(db)
        self.inv = InventoryRepository(db)

    # ---------- Reads ----------
    def get(self, return_id: int) -> ReturnRequest:
        r = self.returns.get(return_id)
        if not r:
            raise NotFound("Return not found")
        return r

    # ---------- Decisions ----------
    def decide(self, return_id: int, approve: bool, reason: Optional[str] = None) -> ReturnRequest:
        r = self.get(return_id)
        if r.status not in {ReturnStatusEnum.requested}:
            raise BadRequest("Only 'requested' returns can be decided")

        with self.db.begin():
            r.status = ReturnStatusEnum.approved if approve else ReturnStatusEnum.rejected
            # If you want to persist reason somewhere: r.reason = reason or r.reason
            self.returns.save(r)

        self.db.refresh(r)
        return r

    def mark_received(self, return_id: int, note: Optional[str] = None) -> ReturnRequest:
        """
        Move approved return to 'received' and restock items.
        """
        r = self.get(return_id)
        if r.status != ReturnStatusEnum.approved:
            raise BadRequest("Return must be 'approved' before marking as received")

        items = self.returns.list_items(r.id)

        with self.db.begin():
            for ri in items:
                if ri.qty <= 0:
                    continue
                # fetch original order item to find the variant
                oi = self.orders.get_item(ri.order_item_id)
                if not oi or not oi.variant_id:
                    continue
                v = self.inv.load_variant(oi.variant_id)
                if not v:
                    continue
                self.inv.change_stock(
                    v,
                    qty_delta=ri.qty,
                    reason=InventoryMovementType.return_in,
                    order_id=r.order_id,
                    note=note or "return received",
                )

            r.status = ReturnStatusEnum.received
            self.returns.save(r)

        self.db.refresh(r)
        return r

    def refund(self, return_id: int, method: PaymentMethodEnum = PaymentMethodEnum.cod) -> ReturnRequest:
        """
        Issue a refund payment and set order + return statuses accordingly.
        Policy here: allow refund after 'approved' or 'received'.
        """
        r = self.get(return_id)
        if r.status not in {ReturnStatusEnum.approved, ReturnStatusEnum.received}:
            raise BadRequest("Return must be 'approved' or 'received' to refund")

        order = r.order
        if not order:
            raise NotFound("Order not found for this return")

        with self.db.begin():
            # Create refund payment (full amount for simplicity)
            self.payments.create(
                order_id=order.id,
                amount_cents=order.total_cents,
                status=PaymentStatusEnum.refunded,
                method=method,
                transaction_ref=None,
            )

            # Update statuses
            r.status = ReturnStatusEnum.refunded
            self.returns.save(r)

            order.status = OrderStatusEnum.refunded
            self.orders.save(order)

        self.db.refresh(r)
        return r

    def close(self, return_id: int) -> ReturnRequest:
        """
        Close a return; typically allowed after refund is processed.
        """
        r = self.get(return_id)
        if r.status not in {ReturnStatusEnum.refunded, ReturnStatusEnum.rejected}:
            raise BadRequest("Only 'refunded' or 'rejected' returns can be closed")

        with self.db.begin():
            r.status = ReturnStatusEnum.closed
            self.returns.save(r)

        self.db.refresh(r)
        return r
