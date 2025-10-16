# app/models/shipment.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.db.enums import ShipmentStatusEnum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.order import Order

class Shipment(Base, TimestampMixin):
    """
    One shipment per order (enforced by unique order_id).
    Tracks carrier/tracking and basic timeline fields.
    """
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    carrier: Mapped[Optional[str]] = mapped_column(String(120))
    tracking_number: Mapped[Optional[str]] = mapped_column(String(120))

    status: Mapped[ShipmentStatusEnum] = mapped_column(
        SAEnum(ShipmentStatusEnum, name="shipment_status", native_enum=False, validate_strings=True),
        default=ShipmentStatusEnum.pending,
        index=True,
        nullable=False,
    )

    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="shipment")

    __table_args__ = (
        # Tracking number uniqueness per carrier (allows multiple NULLs).
        UniqueConstraint("carrier", "tracking_number", name="uq_shipment_carrier_tracking"),
        # Sanity check: delivered_at should not be before shipped_at when both present.
        CheckConstraint(
            "(shipped_at IS NULL) OR (delivered_at IS NULL) OR (delivered_at >= shipped_at)",
            name="ck_shipment_delivered_after_shipped",
        ),
        Index("ix_shipments_order_status", "order_id", "status"),
        Index("ix_shipments_tracking", "carrier", "tracking_number"),
    )

    def __repr__(self) -> str:
        return f"<Shipment id={self.id} order_id={self.order_id} status={self.status} tracking={self.tracking_number!r}>"
