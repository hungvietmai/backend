# app/models/returns.py
from __future__ import annotations

from typing import Optional, List

from sqlalchemy import Integer, String, ForeignKey, CheckConstraint, Index, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.db.enums import ReturnStatusEnum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.order import Order, OrderItem

class ReturnRequest(Base, TimestampMixin):
    """
    A customer's request to return one or more order items.
    Lifecyle controlled by `status` (requested -> approved/rejected -> received -> refunded/closed).
    """
    __tablename__ = "return_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    status: Mapped[ReturnStatusEnum] = mapped_column(
        SAEnum(ReturnStatusEnum, name="return_status", native_enum=False, validate_strings=True),
        default=ReturnStatusEnum.requested,
        index=True,
        nullable=False,
    )

    reason: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    order: Mapped["Order"] = relationship()  # no back_populates to avoid coupling
    items: Mapped[List["ReturnItem"]] = relationship(
        back_populates="return_request",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_returns_order_status_created", "order_id", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ReturnRequest id={self.id} order_id={self.order_id} status={self.status}>"


class ReturnItem(Base, TimestampMixin):
    """
    Line-level return entry that references an original OrderItem.
    We keep a hard reference to OrderItem (RESTRICT) to preserve auditability.
    """
    __tablename__ = "return_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    return_id: Mapped[int] = mapped_column(
        ForeignKey("return_requests.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id", ondelete="RESTRICT"),
        nullable=False,
    )

    qty: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    return_request: Mapped["ReturnRequest"] = relationship(back_populates="items")
    order_item: Mapped["OrderItem"] = relationship()  # from app/models/order.py

    __table_args__ = (
        CheckConstraint("qty > 0", name="ck_return_qty_pos"),
        UniqueConstraint("return_id", "order_item_id", name="uq_returnitem_return_orderitem"),
        Index("ix_return_items_return_created", "return_id", "created_at"),
        Index("ix_return_items_orderitem", "order_item_id"),
    )

    def __repr__(self) -> str:
        return f"<ReturnItem id={self.id} return_id={self.return_id} order_item_id={self.order_item_id} qty={self.qty}>"
