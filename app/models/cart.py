# app/models/cart.py
from __future__ import annotations

from typing import List

from sqlalchemy import (
    Integer,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from app.db.base import Base
from app.db.mixins import TimestampMixin, SoftDeleteMixin
from app.db.enums import CartStatusEnum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.auth import User
    from app.models.catalog import ProductVariant


class Cart(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    status: Mapped[CartStatusEnum] = mapped_column(
        SAEnum(CartStatusEnum, name="cart_status", native_enum=False, validate_strings=True),
        default=CartStatusEnum.open,
        index=True,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="carts")
    items: Mapped[List["CartItem"]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
    )

    # One open (and not soft-deleted) cart per user:
    __table_args__ = (
        Index(
            "uq_cart_user_open",
            "user_id",
            unique=True,
            sqlite_where=text("status = 'open' AND deleted_at IS NULL"),
            postgresql_where=text("status = 'open' AND deleted_at IS NULL"),
        ),
    )

    def __repr__(self) -> str:
        return f"<Cart id={self.id} user_id={self.user_id} status={self.status} deleted={self.deleted_at is not None}>"


class CartItem(Base, TimestampMixin):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    variant_id: Mapped[int] = mapped_column(
        ForeignKey("product_variants.id"),
        index=True,
        nullable=False,
    )

    qty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    cart: Mapped["Cart"] = relationship(back_populates="items")
    variant: Mapped["ProductVariant"] = relationship()  # from app/models/catalog.py

    __table_args__ = (
        UniqueConstraint("cart_id", "variant_id", name="uq_cartitem_cart_variant"),
        CheckConstraint("qty > 0", name="ck_cartitem_qty_pos"),
        CheckConstraint("unit_price_cents >= 0", name="ck_cartitem_unit_price_nonneg"),
        CheckConstraint("line_total_cents >= 0", name="ck_cartitem_line_total_nonneg"),
        Index("ix_cart_items_cart_created", "cart_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<CartItem id={self.id} cart_id={self.cart_id} variant_id={self.variant_id} qty={self.qty}>"
