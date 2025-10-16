# app/services/order_service.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.repositories.cart_repo import CartRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.payment_repo import PaymentRepository
from app.repositories.inventory_repo import InventoryRepository

from app.schemas.order import OrderOut
from app.schemas.page import Page
from app.utils.orders import gen_order_number
from app.exceptions import NotFound, BadRequest
from app.models.order import Order
from app.db.enums import (
    OrderStatusEnum, PaymentStatusEnum, PaymentMethodEnum,
    InventoryMovementType,
)


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.carts = CartRepository(db)
        self.orders = OrderRepository(db)
        self.payments = PaymentRepository(db)
        self.inv = InventoryRepository(db)

    # -------- User list as Page --------
    def list_my_orders_page(
        self,
        user_id: int,
        *,
        status: Optional[List[str]] = None,
        created_from=None,
        created_to=None,
        min_total: int | None = None,
        max_total: int | None = None,
        sort: list[str] = ["-created_at"],
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

    # -------- Admin list as Page --------
    def list_admin_orders_page(
        self,
        *,
        user_id: int | None = None,
        status: Optional[List[str]] = None,
        created_from=None,
        created_to=None,
        min_total: int | None = None,
        max_total: int | None = None,
        sort: list[str] = ["-created_at"],
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

    def get_for_user(self, user_id: int, order_id: int) -> Order:
        o = self.orders.get(order_id)
        if not o or o.user_id != user_id:
            raise NotFound(detail="Order not found")
        return o

    # ---- Checkout ----
    def checkout(
        self,
        user_id: int,
        shipping: dict,
        payment_method: PaymentMethodEnum,
        pay_now: bool,
        shipping_fee_cents: int,
    ) -> Order:
        cart = self.carts.get_open_for_user(user_id)
        if not cart or not cart.items:
            raise BadRequest(detail="Cart is empty")

        # Recompute subtotal & validate stock/availability
        subtotal = 0
        for it in cart.items:
            v = self.inv.load_variant(it.variant_id)
            if not v or not v.product or not v.product.is_active:
                raise BadRequest(detail=f"Variant {it.variant_id} unavailable")
            if it.qty > (v.stock_qty or 0):
                raise BadRequest(detail=f"Insufficient stock for variant {it.variant_id}")
            subtotal += it.line_total_cents

        total = subtotal + int(shipping_fee_cents or 0)
        now = datetime.now(timezone.utc)

        with self.db.begin():
            # 1) create order (snapshot shipping)
            o = self.orders.create({
                "order_number": gen_order_number(),
                "user_id": user_id,
                "status": OrderStatusEnum.pending,
                "subtotal_cents": subtotal,
                "shipping_fee_cents": shipping_fee_cents,
                "discount_cents": 0,
                "total_cents": total,
                "currency": "VND",
                "ship_full_name": shipping["full_name"],
                "ship_mobile_num": shipping["mobile_num"],
                "ship_detail_address": shipping["detail_address"],
                "ship_province_name": shipping.get("province_name"),
                "ship_district_name": shipping.get("district_name"),
                "ship_ward_name": shipping.get("ward_name"),
                "ship_zip_code": shipping.get("zip_code"),
            })

            # 2) add items & decrement stock with ledger
            for it in cart.items:
                v = self.inv.load_variant(it.variant_id)
                # v cannot be None here due to earlier checks, but keep it safe:
                if not v or not v.product or not v.product.is_active:
                    raise BadRequest(detail=f"Variant {it.variant_id} unavailable")

                self.inv.change_stock(
                    v, -it.qty, InventoryMovementType.sold,
                    order_id=o.id, note="checkout"
                )

                self.orders.add_item(
                    o.id,
                    {
                        "product_id": v.product_id,
                        "variant_id": v.id,
                        "name": v.product.name,
                        "sku": v.sku,
                        "color": v.color,
                        "size": v.size,
                        "qty": it.qty,
                        "unit_price_cents": it.unit_price_cents,
                        "line_total_cents": it.line_total_cents,
                    },
                )

            # 3) mark cart checked out
            self.carts.set_checked_out(cart)

            # 4) create payment row
            p_status = PaymentStatusEnum.paid if pay_now else PaymentStatusEnum.pending
            self.payments.create(
                o.id,
                amount_cents=o.total_cents,
                status=p_status,
                method=payment_method,
                transaction_ref=None,
            )

            # 5) update order status if paid now
            if pay_now:
                o.status = OrderStatusEnum.paid
                o.paid_at = now
                self.orders.save(o)

        self.db.refresh(o)
        return o

    # ---- User: pay (simulate capture) ----
    def pay(self, user_id: int, order_id: int, method: PaymentMethodEnum) -> Order:
        o = self.get_for_user(user_id, order_id)
        if o.status not in {OrderStatusEnum.pending}:
            raise BadRequest(detail="Order cannot be paid")

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
            o.paid_at = now
            self.orders.save(o)

        self.db.refresh(o)
        return o

    # ---- User: cancel ----
    def cancel(self, user_id: int, order_id: int) -> Order:
        o = self.get_for_user(user_id, order_id)
        if o.status not in {OrderStatusEnum.pending}:
            raise BadRequest(detail="Order cannot be cancelled at this stage")

        now = datetime.now(timezone.utc)
        with self.db.begin():
            # return stock
            for it in o.items:
                if it.variant_id:
                    v = self.inv.load_variant(it.variant_id)
                    if v:
                        self.inv.change_stock(
                            v, +it.qty, InventoryMovementType.cancel_adjust,
                            order_id=o.id, note="cancel"
                        )
            o.status = OrderStatusEnum.cancelled
            o.cancelled_at = now
            self.orders.save(o)

        self.db.refresh(o)
        return o

    # ---- Admin: mark fulfilled ----
    def mark_fulfilled(self, order_id: int) -> Order:
        o = self.orders.get(order_id)
        if not o:
            raise NotFound(detail="Order not found")
        if o.status not in {OrderStatusEnum.paid}:
            raise BadRequest(detail="Only paid orders can be fulfilled")

        now = datetime.now(timezone.utc)
        with self.db.begin():
            o.status = OrderStatusEnum.fulfilled
            o.fulfilled_at = now
            self.orders.save(o)

        self.db.refresh(o)
        return o
