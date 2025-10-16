# app/models/order.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, SoftDeleteMixin
from app.db.enums import OrderStatusEnum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.auth import User
    from app.models.payment import Payment
    from app.models.shipment import Shipment

class Order(Base, TimestampMixin, SoftDeleteMixin):
    """
    Customer order (financial record).
    - Soft delete is allowed for business needs, but generally avoid hard deletes.
    - Shipping fields are snapshotted to preserve history even if the Address/User changes.
    """
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)  # e.g., FS-20251015-0001

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    status: Mapped[OrderStatusEnum] = mapped_column(
        SAEnum(OrderStatusEnum, name="order_status", native_enum=False, validate_strings=True),
        default=OrderStatusEnum.pending,
        index=True,
        nullable=False,
    )

    # amounts
    subtotal_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shipping_fee_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="VND", nullable=False)

    # timeline
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # shipping snapshot (denormalized from Address at checkout)
    ship_full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ship_mobile_num: Mapped[str] = mapped_column(String(20), nullable=False)
    ship_detail_address: Mapped[str] = mapped_column(String(500), nullable=False)
    ship_province_name: Mapped[Optional[str]] = mapped_column(String(100))
    ship_district_name: Mapped[Optional[str]] = mapped_column(String(100))
    ship_ward_name: Mapped[Optional[str]] = mapped_column(String(100))
    ship_zip_code: Mapped[Optional[str]] = mapped_column(String(20))

    # relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    payments: Mapped[List["Payment"]] = relationship(  # defined in app/models/payment.py
        back_populates="order",
        cascade="all, delete-orphan",
    )
    shipment: Mapped[Optional["Shipment"]] = relationship(  # defined in app/models/shipment.py
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("subtotal_cents >= 0", name="ck_order_subtotal_nonneg"),
        CheckConstraint("shipping_fee_cents >= 0", name="ck_order_shipfee_nonneg"),
        CheckConstraint("discount_cents >= 0", name="ck_order_discount_nonneg"),
        CheckConstraint("total_cents >= 0", name="ck_order_total_nonneg"),
        Index("ix_orders_user_status_created", "user_id", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} no={self.order_number!r} status={self.status} total={self.total_cents}>"


class OrderItem(Base, TimestampMixin):
    """
    Order line item.
    - Keeps product/variant references nullable so history remains if catalog rows are removed/archived.
    - Stores a textual snapshot (name, sku, color, size) for stable invoices.
    """
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # nullable links to catalog to preserve history
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))
    variant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_variants.id", ondelete="SET NULL"))

    # snapshot fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(64))
    size: Mapped[Optional[str]] = mapped_column(String(32))

    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")

    __table_args__ = (
        CheckConstraint("qty > 0", name="ck_orderitem_qty_pos"),
        CheckConstraint("unit_price_cents >= 0", name="ck_orderitem_unit_price_nonneg"),
        CheckConstraint("line_total_cents >= 0", name="ck_orderitem_line_total_nonneg"),
        Index("ix_order_items_order_created", "order_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<OrderItem id={self.id} order_id={self.order_id} sku={self.sku!r} qty={self.qty}>"
