from __future__ import annotations
from typing import List
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.repositories.catalog_repo import CatalogRepository
from app.schemas.page import Page
from app.schemas.catalog import BrandOut, CategoryOut
from app.exceptions import NotFound, Conflict, BadRequest


class AdminCatalogService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CatalogRepository(db)

    # ---------- Brands ----------
    def list_brands_page(self, *, q: str | None, sort: List[str] | None, limit: int, offset: int) -> Page[BrandOut]:
        items, total = self.repo.list_brands(q=q, sort=sort or ["name"], limit=limit, offset=offset)
        dto = [BrandOut.model_validate(b, from_attributes=True) for b in items]
        return Page[BrandOut].from_parts(dto, total, limit, offset)

    def get_brand(self, brand_id: int) -> BrandOut:
        row = self.repo.get_brand(brand_id)
        if not row:
            raise NotFound("Brand not found")
        return BrandOut.model_validate(row, from_attributes=True)

    def create_brand(self, data: dict):
        # No get_brand_by_slug in repo; rely on DB unique or add your own check elsewhere.
        with self.db.begin():
            row = self.repo.create_brand(data)
        self.db.refresh(row)
        return row

    def update_brand(self, brand_id: int, data: dict):
        row = self.repo.get_brand(brand_id)
        if not row:
            raise NotFound("Brand not found")
        with self.db.begin():
            row = self.repo.update_brand(row, data)
        self.db.refresh(row)
        return row

    def delete_brand(self, brand_id: int, *, hard: bool = False):
        row = self.repo.get_brand(brand_id)
        if not row:
            raise NotFound("Brand not found")
        with self.db.begin():
            if hard:
                self.repo.delete_brand(row)
            else:
                # Soft-delete via SoftDeleteMixin (repo exposes update only)
                self.repo.update_brand(row, {"deleted_at": datetime.now(timezone.utc)})

    # ---------- Categories ----------
    def list_categories_page(self, *, q: str | None, parent_id: int | None, sort: List[str] | None, limit: int, offset: int) -> Page[CategoryOut]:
        items, total = self.repo.list_categories(q=q, parent_id=parent_id, sort=sort or ["name"], limit=limit, offset=offset)
        dto = [CategoryOut.model_validate(c, from_attributes=True) for c in items]
        return Page[CategoryOut].from_parts(dto, total, limit, offset)

    def get_category(self, category_id: int) -> CategoryOut:
        row = self.repo.get_category(category_id)
        if not row:
            raise NotFound("Category not found")
        return CategoryOut.model_validate(row, from_attributes=True)

    def create_category(self, data: dict):
        with self.db.begin():
            row = self.repo.create_category(data)
        self.db.refresh(row)
        return row

    def update_category(self, category_id: int, data: dict):
        row = self.repo.get_category(category_id)
        if not row:
            raise NotFound("Category not found")
        with self.db.begin():
            row = self.repo.update_category(row, data)
        self.db.refresh(row)
        return row

    def move_category(self, category_id: int, parent_id: int | None):
        row = self.repo.get_category(category_id)
        if not row:
            raise NotFound("Category not found")
        with self.db.begin():
            row = self.repo.update_category(row, {"parent_id": parent_id})
        self.db.refresh(row)
        return row

    def delete_category(self, category_id: int, *, hard: bool = False):
        row = self.repo.get_category(category_id)
        if not row:
            raise NotFound("Category not found")

        # Optional safety: block hard delete if category has children
        if hard and self.repo.has_children(category_id):
            raise BadRequest("Cannot hard-delete a category that has children")

        with self.db.begin():
            if hard:
                self.repo.delete_category(row)
            else:
                self.repo.update_category(row, {"deleted_at": datetime.now(timezone.utc)})
