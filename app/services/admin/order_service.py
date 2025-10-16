# app/services/admin/order_service.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List, cast

from sqlalchemy.orm import Session

from app.repositories.order_repo import OrderRepository
from app.repositories.payment_repo import PaymentRepository
from app.repositories.shipment_repo import ShipmentRepository
from app.repositories.inventory_repo import InventoryRepository

from app.schemas.page import Page
from app.schemas.order import OrderOut
from app.db.enums import (
    OrderStatusEnum,
    PaymentStatusEnum,
    PaymentMethodEnum,
    ShipmentStatusEnum,
    InventoryMovementType,
)
from app.exceptions import NotFound, BadRequest


class AdminOrderService:
    """Business rules for admin order actions. Owns transactions and side effects."""
    def __init__(self, db: Session):
        self.db = db
        self.orders = OrderRepository(db)
        self.payments = PaymentRepository(db)
        self.shipments = ShipmentRepository(db)
        self.inv = InventoryRepository(db)

    # ---------- Read / List ----------
    def list_page(
        self,
        *,
        user_id: int | None = None,
        status: Optional[List[str]] = None,
        created_from=None,
        created_to=None,
        min_total: int | None = None,
        max_total: int | None = None,
        sort: List[str] = ["-created_at"],
        limit: int = 50,
        offset: int = 0,
    ) -> Page[OrderOut]:
        items, total = self.orders.list_paged(
            user_id=user_id,
            status=status,
            created_from=created_from,
            created_to=created_to,
            min_total=min_total,
            max_total=max_total,
            sort=sort,
            limit=limit,
            offset=offset,
        )
        dto = [OrderOut.model_validate(o, from_attributes=True) for o in items]
        return Page[OrderOut].from_parts(dto, total, limit, offset)

    def _get_or_404(self, order_id: int):
        o = self.orders.get(order_id)
        if not o:
            raise NotFound("Order not found")
        return o

    # ---------- Transitions ----------
    def mark_paid(self, order_id: int, method: PaymentMethodEnum = PaymentMethodEnum.momo):
        """Record a successful payment and move order to 'paid'."""
        o = self._get_or_404(order_id)
        if o.status not in {OrderStatusEnum.pending}:
            raise BadRequest("Only 'pending' orders can be marked as paid")

        now = datetime.now(timezone.utc)
        with self.db.begin():
            self.payments.create(
                o.id,
                amount_cents=o.total_cents,
                status=PaymentStatusEnum.paid,
                method=method,
                transaction_ref=None,
            )
            o.status = OrderStatusEnum.paid
            o.paid_at = cast("datetime | None", now)
            self.orders.save(o)

        self.db.refresh(o)
        return o

    def cancel(self, order_id: int):
        """Cancel a pending order and return stock."""
        o = self._get_or_404(order_id)
        if o.status not in {OrderStatusEnum.pending}:
            raise BadRequest("Only 'pending' orders can be cancelled")

        now = datetime.now(timezone.utc)
        with self.db.begin():
            for it in o.items:
                if it.variant_id:
                    v = self.inv.load_variant(it.variant_id)
                    if v:
                        self.inv.change_stock(
                            v, +it.qty, InventoryMovementType.cancel_adjust,
                            order_id=o.id, note="admin cancel"
                        )
            o.status = OrderStatusEnum.cancelled
            o.cancelled_at = cast("datetime | None", now)
            self.orders.save(o)

        self.db.refresh(o)
        return o

    def create_shipment(self, order_id: int, carrier: str | None = None, tracking: str | None = None):
        """
        Create (or get) a shipment for an order.
        Common policy: allow only for paid orders (adjust if you want).
        """
        o = self._get_or_404(order_id)
        if o.status not in {OrderStatusEnum.paid, OrderStatusEnum.fulfilled}:
            raise BadRequest("Shipment can be created only for paid/fulfilled orders")

        with self.db.begin():
            s = self.shipments.get_by_order(o.id)
            if not s:
                s = self.shipments.create(
                    o.id,
                    {"carrier": carrier, "tracking_number": tracking, "status": ShipmentStatusEnum.packed},
                )
            else:
                self.shipments.update(s, {"carrier": carrier, "tracking_number": tracking})

        self.db.refresh(o)
        return o.shipment

    def update_shipment(
        self,
        order_id: int,
        *,
        status: ShipmentStatusEnum,
        carrier: str | None = None,
        tracking: str | None = None,
        shipped_at_iso: str | None = None,
        delivered_at_iso: str | None = None,
    ):
        """Update shipment; if delivered and order is paid → mark fulfilled."""
        o = self._get_or_404(order_id)

        def _parse_iso(ts: str | None):
            if not ts:
                return None
            dt = datetime.fromisoformat(ts)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

        shipped_dt = _parse_iso(shipped_at_iso)
        delivered_dt = _parse_iso(delivered_at_iso)

        with self.db.begin():
            s = self.shipments.get_by_order(o.id)
            if not s:
                s = self.shipments.create(
                    o.id,
                    {
                        "carrier": carrier,
                        "tracking_number": tracking,
                        "status": status,
                        "shipped_at": shipped_dt,
                        "delivered_at": delivered_dt,
                    },
                )
            else:
                self.shipments.update(
                    s,
                    {
                        "status": status,
                        "carrier": carrier,
                        "tracking_number": tracking,
                        "shipped_at": shipped_dt,
                        "delivered_at": delivered_dt,
                    },
                )

            # Optional fulfillment auto-transition
            if status == ShipmentStatusEnum.delivered and o.status == OrderStatusEnum.paid:
                o.status = OrderStatusEnum.fulfilled
                o.fulfilled_at = cast("datetime | None", datetime.now(timezone.utc))
                self.orders.save(o)

        self.db.refresh(o)
        return o.shipment

    def refund_order(self, order_id: int, reason: str | None = None):
        """Full order refund; adds stock back and records a refund payment."""
        o = self._get_or_404(order_id)
        if o.status not in {OrderStatusEnum.paid, OrderStatusEnum.fulfilled}:
            raise BadRequest("Only 'paid' or 'fulfilled' orders can be refunded")

        with self.db.begin():
            # Restock items
            for it in o.items:
                if it.variant_id:
                    v = self.inv.load_variant(it.variant_id)
                    if v:
                        self.inv.change_stock(
                            v, +it.qty, InventoryMovementType.return_in,
                            order_id=o.id, note=reason or "refund"
                        )

            # Record refund payment
            self.payments.create(
                o.id,
                amount_cents=o.total_cents,
                status=PaymentStatusEnum.refunded,
                method=PaymentMethodEnum.cod,  # or track original method if you prefer
                transaction_ref=None,
            )

            # Update order status
            o.status = OrderStatusEnum.refunded
            self.orders.save(o)

        self.db.refresh(o)
        return o
