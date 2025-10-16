from __future__ import annotations
from typing import Optional, List, Sequence, Tuple
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.common.listing import paginate, safe_order_by, ilike_any, Col
from app.models.catalog import (
    Product, ProductVariant, ProductImage, ProductCategory
)

ALLOWED_SORT: dict[str, Col] = {
    "id": Product.id,
    "name": Product.name,
    "slug": Product.slug,
    "price": Product.base_price_cents,
    "created_at": Product.created_at,
    "updated_at": Product.updated_at,
    "is_active": Product.is_active,
    "is_archived": Product.is_archived,
}
DEFAULT_SORT = ["-created_at"]


class ProductRepository:
    """Role-agnostic persistence utilities for products/variants/images. No commits here."""
    def __init__(self, db: Session):
        self.db = db

    # ---------- Product: reads ----------
    def get(self, product_id: int) -> Optional[Product]:
        return self.db.get(Product, product_id)

    def get_by_slug(self, slug: str) -> Optional[Product]:
        stmt = select(Product).where(Product.slug == slug, Product.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def list_paged(
        self,
        *,
        q: str | None,
        brand_id: int | None,
        category_id: int | None,
        is_active: bool | None,
        is_archived: bool | None,
        price_min: int | None,
        price_max: int | None,
        sort: List[str],
        limit: int,
        offset: int,
    ) -> Tuple[List[Product], int]:
        stmt: Select[tuple[Product]] = select(Product).where(Product.deleted_at.is_(None))

        conds = []
        if q:
            conds.append(ilike_any([Product.name, Product.slug, Product.description], q))
        if brand_id is not None:
            conds.append(Product.brand_id == brand_id)
        if category_id is not None:
            # product in category via junction table
            sub = select(ProductCategory.product_id).where(ProductCategory.category_id == category_id)
            conds.append(Product.id.in_(sub))
        if is_active is not None:
            conds.append(Product.is_active == is_active)
        if is_archived is not None:
            conds.append(Product.is_archived == is_archived)
        if price_min is not None:
            conds.append(Product.base_price_cents >= price_min)
        if price_max is not None:
            conds.append(Product.base_price_cents <= price_max)

        if conds:
            stmt = stmt.where(and_(*conds))

        stmt = stmt.order_by(*safe_order_by(sort, ALLOWED_SORT, DEFAULT_SORT))
        return paginate(self.db, stmt, limit, offset)

    # ---------- Product: writes (no commit) ----------
    def create(self, data: dict) -> Product:
        row = Product(**data)
        self.db.add(row)
        return row

    def update(self, row: Product, data: dict) -> Product:
        for k, v in data.items():
            setattr(row, k, v)
        self.db.add(row)
        return row

    def delete(self, row: Product) -> None:
        self.db.delete(row)

    # ---------- Variants ----------
    def get_variant(self, variant_id: int) -> Optional[ProductVariant]:
        return self.db.get(ProductVariant, variant_id)

    def list_variants(self, product_id: int) -> Sequence[ProductVariant]:
        stmt = select(ProductVariant).where(
            ProductVariant.product_id == product_id,
            ProductVariant.deleted_at.is_(None)
        ).order_by(ProductVariant.created_at.desc())
        return self.db.execute(stmt).scalars().all()

    def create_variant(self, product_id: int, data: dict) -> ProductVariant:
        row = ProductVariant(product_id=product_id, **data)
        self.db.add(row)
        return row

    def update_variant(self, row: ProductVariant, data: dict) -> ProductVariant:
        for k, v in data.items():
            setattr(row, k, v)
        self.db.add(row)
        return row

    def delete_variant(self, row: ProductVariant) -> None:
        self.db.delete(row)

    # ---------- Images ----------
    def list_images(self, product_id: int) -> Sequence[ProductImage]:
        stmt = select(ProductImage).where(ProductImage.product_id == product_id).order_by(
            ProductImage.is_primary.desc(), ProductImage.sort_order.asc(), ProductImage.id.asc()
        )
        return self.db.execute(stmt).scalars().all()

    def add_image(self, product_id: int, data: dict) -> ProductImage:
        row = ProductImage(product_id=product_id, **data)
        self.db.add(row)
        return row

    def get_image(self, image_id: int) -> Optional[ProductImage]:
        return self.db.get(ProductImage, image_id)

    def update_image(self, row: ProductImage, data: dict) -> ProductImage:
        for k, v in data.items():
            setattr(row, k, v)
        self.db.add(row)
        return row

    def delete_image(self, row: ProductImage) -> None:
        self.db.delete(row)
