# app/models/payment.py
from __future__ import annotations

from typing import Optional

from sqlalchemy import Integer, String, ForeignKey, CheckConstraint, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.db.enums import PaymentStatusEnum, PaymentMethodEnum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.order import Order

class Payment(Base, TimestampMixin):
    """
    Payment record tied to an Order.
    - Keep rows immutable for audit when possible; corrections should be new rows (e.g., refunds/voids).
    - `transaction_ref` can hold gateway txn id / bank code.
    """
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[PaymentStatusEnum] = mapped_column(
        SAEnum(PaymentStatusEnum, name="payment_status", native_enum=False, validate_strings=True),
        default=PaymentStatusEnum.pending,
        index=True,
        nullable=False,
    )

    method: Mapped[PaymentMethodEnum] = mapped_column(
        SAEnum(PaymentMethodEnum, name="payment_method", native_enum=False, validate_strings=True),
        default=PaymentMethodEnum.cod,
        index=True,
        nullable=False,
    )

    transaction_ref: Mapped[Optional[str]] = mapped_column(String(255))

    # relationships
    order: Mapped["Order"] = relationship(back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount_cents >= 0", name="ck_payment_amount_nonneg"),
        Index("ix_payments_order_created", "order_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Payment id={self.id} order_id={self.order_id} amount={self.amount_cents} status={self.status} method={self.method}>"
