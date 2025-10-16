# app/models/inventory.py
from __future__ import annotations

from typing import Optional

from sqlalchemy import Integer, String, ForeignKey, CheckConstraint, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.db.enums import InventoryMovementType

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.catalog import ProductVariant

class InventoryMovement(Base, TimestampMixin):
    """
    Immutable inventory ledger row. Prefer *appending* new rows over editing past rows.
    Use qty_delta > 0 for inflows (stock_in, return_in, cancel_adjust, manual_adjust+),
    and qty_delta < 0 for outflows (reserve, sold, manual_adjust-, etc.).
    """
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    variant_id: Mapped[int] = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    qty_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[InventoryMovementType] = mapped_column(
        SAEnum(InventoryMovementType, name="inventory_movement", native_enum=False, validate_strings=True),
        index=True,
        nullable=False,
    )
    note: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships (string targets avoid cross-file imports)
    variant: Mapped["ProductVariant"] = relationship()          # from app/models/catalog.py
    order: Mapped[Optional["Order"]] = relationship(back_populates="")  # optional; usually not back-populated

    __table_args__ = (
        # Disallow zero deltas; every movement must change stock.
        CheckConstraint("qty_delta <> 0", name="ck_inventory_qty_nonzero"),
        # Common read pattern: per-variant chronological scans.
        Index("ix_inventory_variant_created", "variant_id", "created_at"),
    )

    # Convenience flags
    @property
    def is_inflow(self) -> bool:
        return self.qty_delta > 0

    @property
    def is_outflow(self) -> bool:
        return self.qty_delta < 0

    def __repr__(self) -> str:
        return f"<InvMove id={self.id} variant_id={self.variant_id} delta={self.qty_delta} reason={self.reason}>"
