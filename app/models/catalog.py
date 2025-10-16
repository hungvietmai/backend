from __future__ import annotations

from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    Text,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, SoftDeleteMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.review import Review

class Brand(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)

    products: Mapped[List["Product"]] = relationship(
        back_populates="brand",
    )

    def __repr__(self) -> str:
        return f"<Brand id={self.id} name={self.name!r}>"


class Category(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)

    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL")
    )
    parent: Mapped[Optional["Category"]] = relationship(remote_side="Category.id")

    # Through table
    products: Mapped[List["ProductCategory"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name!r}>"


class Product(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    brand_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("brands.id", ondelete="SET NULL")
    )

    description: Mapped[Optional[str]] = mapped_column(Text)
    base_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="VND", nullable=False)

    # Catalog visibility
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)

    brand: Mapped[Optional["Brand"]] = relationship(back_populates="products")

    variants: Mapped[List["ProductVariant"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    images: Mapped[List["ProductImage"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    categories: Mapped[List["ProductCategory"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[List["Review"]] = relationship(  # defined in app/models/review.py
        back_populates="product",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("base_price_cents >= 0", name="ck_product_price_nonneg"),
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} slug={self.slug!r} active={self.is_active}>"


class ProductVariant(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    color: Mapped[Optional[str]] = mapped_column(String(64))
    size: Mapped[Optional[str]] = mapped_column(String(32))

    stock_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    price_cents: Mapped[Optional[int]] = mapped_column(Integer)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))

    product: Mapped["Product"] = relationship(back_populates="variants")

    __table_args__ = (
        UniqueConstraint("product_id", "color", "size", name="uq_variant_product_color_size"),
        CheckConstraint("stock_qty >= 0", name="ck_variant_stock_nonneg"),
        CheckConstraint("price_cents IS NULL OR price_cents >= 0", name="ck_variant_price_nonneg"),
    )

    def __repr__(self) -> str:
        return f"<Variant id={self.id} sku={self.sku!r} stock={self.stock_qty}>"


class ProductImage(Base, TimestampMixin):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="images")

    def __repr__(self) -> str:
        return f"<ProductImage id={self.id} product_id={self.product_id} primary={self.is_primary}>"


class ProductCategory(Base):
    """
    Many-to-many association between Product and Category.
    """
    __tablename__ = "product_categories"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
    )

    product: Mapped["Product"] = relationship(back_populates="categories")
    category: Mapped["Category"] = relationship(back_populates="products")

    def __repr__(self) -> str:
        return f"<ProductCategory product_id={self.product_id} category_id={self.category_id}>"
