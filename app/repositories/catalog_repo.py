from __future__ import annotations
from typing import List, Tuple, Sequence
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.common.listing import paginate, safe_order_by, ilike_any, Col
from app.models.catalog import Brand, Category

ALLOWED_BRAND_SORT: dict[str, Col] = {
    "id": Brand.id, "name": Brand.name, "slug": Brand.slug, "created_at": Brand.created_at,
}
ALLOWED_CATEGORY_SORT: dict[str, Col] = {
    "id": Category.id, "name": Category.name, "slug": Category.slug, "parent_id": Category.parent_id, "created_at": Category.created_at,
}
DEFAULT_SORT_BRAND = ["name"]
DEFAULT_SORT_CATEGORY = ["name"]


class CatalogRepository:
    """Unified repo for brands & categories (public + admin). No commits here."""
    def __init__(self, db: Session):
        self.db = db

    # ---- Brands (read) ----
    def list_brands(self, *, q: str | None, sort: List[str], limit: int, offset: int) -> Tuple[List[Brand], int]:
        stmt: Select[tuple[Brand]] = select(Brand).where(Brand.deleted_at.is_(None))
        if q:
            stmt = stmt.where(ilike_any([Brand.name, Brand.slug], q))
        stmt = stmt.order_by(*safe_order_by(sort, ALLOWED_BRAND_SORT, DEFAULT_SORT_BRAND))
        return paginate(self.db, stmt, limit, offset)

    def get_brand(self, brand_id: int) -> Brand | None:
        return self.db.get(Brand, brand_id)

    # ---- Brands (write) ----
    def create_brand(self, data: dict) -> Brand:
        row = Brand(**data); self.db.add(row); return row

    def update_brand(self, row: Brand, data: dict) -> Brand:
        for k, v in data.items(): setattr(row, k, v)
        self.db.add(row); return row

    def delete_brand(self, row: Brand) -> None:
        self.db.delete(row)

    # ---- Categories (read) ----
    def list_categories(
        self, *, q: str | None, parent_id: int | None, sort: List[str], limit: int, offset: int
    ) -> Tuple[List[Category], int]:
        stmt: Select[tuple[Category]] = select(Category).where(Category.deleted_at.is_(None))
        conds = []
        if q: conds.append(ilike_any([Category.name, Category.slug], q))
        if parent_id is not None: conds.append(Category.parent_id == parent_id)
        if conds: stmt = stmt.where(and_(*conds))
        stmt = stmt.order_by(*safe_order_by(sort, ALLOWED_CATEGORY_SORT, DEFAULT_SORT_CATEGORY))
        return paginate(self.db, stmt, limit, offset)

    def get_category(self, category_id: int) -> Category | None:
        return self.db.get(Category, category_id)

    def all_categories(self) -> Sequence[Category]:
        return self.db.execute(
            select(Category).where(Category.deleted_at.is_(None)).order_by(Category.parent_id.nullsfirst(), Category.name)
        ).scalars().all()

    def has_children(self, category_id: int) -> bool:
        cnt = self.db.scalar(select(func.count()).select_from(Category).where(Category.parent_id == category_id)) or 0
        return cnt > 0

    # ---- Categories (write) ----
    def create_category(self, data: dict) -> Category:
        row = Category(**data); self.db.add(row); return row

    def update_category(self, row: Category, data: dict) -> Category:
        for k, v in data.items(): setattr(row, k, v)
        self.db.add(row); return row

    def delete_category(self, row: Category) -> None:
        self.db.delete(row)
