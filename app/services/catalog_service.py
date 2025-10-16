# app/services/catalog_service.py
from __future__ import annotations
from typing import List, Optional, Sequence

from sqlalchemy.orm import Session

from app.repositories.catalog_repo import CatalogRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.page import Page
from app.schemas.catalog import BrandOut, CategoryOut, CategoryNodeOut
from app.schemas.product import ProductOut
from app.exceptions import NotFound


class CatalogService:
    def __init__(self, db: Session):
        self.db = db
        self.catalog = CatalogRepository(db)
        self.products = ProductRepository(db)

    # ---------- Brands ----------
    def list_brands_page(
        self,
        *,
        q: Optional[str] = None,
        sort: List[str] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Page[BrandOut]:
        items, total = self.catalog.list_brands(q=(q or None), sort=sort or ["name"], limit=limit, offset=offset)
        dto = [BrandOut.model_validate(b, from_attributes=True) for b in items]
        return Page[BrandOut].from_parts(dto, total, limit, offset)

    def get_brand(self, brand_id: int) -> BrandOut:
        b = self.catalog.get_brand(brand_id)
        if not b or getattr(b, "deleted_at", None) is not None:
            raise NotFound("Brand not found")
        return BrandOut.model_validate(b, from_attributes=True)

    # ---------- Categories ----------
    def list_categories_page(
        self,
        *,
        q: Optional[str] = None,
        parent_id: int | None = None,
        sort: List[str] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Page[CategoryOut]:
        items, total = self.catalog.list_categories(
            q=(q or None), parent_id=parent_id, sort=sort or ["name"], limit=limit, offset=offset
        )
        dto = [CategoryOut.model_validate(c, from_attributes=True) for c in items]
        return Page[CategoryOut].from_parts(dto, total, limit, offset)

    def get_category(self, category_id: int) -> CategoryOut:
        c = self.catalog.get_category(category_id)
        if not c or getattr(c, "deleted_at", None) is not None:
            raise NotFound("Category not found")
        return CategoryOut.model_validate(c, from_attributes=True)

    def category_tree(self) -> list[CategoryNodeOut]:
        rows = self.catalog.all_categories()
        # index → nodes
        nodes: dict[int, CategoryNodeOut] = {
            r.id: CategoryNodeOut(id=r.id, name=r.name, slug=r.slug, parent_id=r.parent_id, children=[])
            for r in rows
        }
        roots: list[CategoryNodeOut] = []
        for r in rows:
            node = nodes[r.id]
            if r.parent_id and r.parent_id in nodes:
                nodes[r.parent_id].children.append(node)
            else:
                roots.append(node)
        return roots

    # ---------- Product listings scoped by brand/category ----------
    def list_products_by_brand_page(
        self,
        brand_id: int,
        *,
        q: Optional[str] = None,
        sort: List[str] | None = None,
        limit: int = 50,
        offset: int = 0,
        validate_exists: bool = False,  # set True if you want 404 when brand missing
    ) -> Page[ProductOut]:
        if validate_exists:
            b = self.catalog.get_brand(brand_id)
            if not b or getattr(b, "deleted_at", None) is not None:
                raise NotFound("Brand not found")

        items, total = self.products.list_paged(
            q=(q or None),
            brand_id=brand_id,
            category_id=None,
            is_active=True,
            is_archived=False,
            price_min=None,
            price_max=None,
            sort=sort or ["-created_at"],
            limit=limit,
            offset=offset,
        )
        dto = [ProductOut.model_validate(p, from_attributes=True) for p in items]
        return Page[ProductOut].from_parts(dto, total, limit, offset)

    def list_products_by_category_page(
        self,
        category_id: int,
        *,
        q: Optional[str] = None,
        sort: List[str] | None = None,
        limit: int = 50,
        offset: int = 0,
        validate_exists: bool = False,  # set True if you want 404 when category missing
    ) -> Page[ProductOut]:
        if validate_exists:
            c = self.catalog.get_category(category_id)
            if not c or getattr(c, "deleted_at", None) is not None:
                raise NotFound("Category not found")

        items, total = self.products.list_paged(
            q=(q or None),
            brand_id=None,
            category_id=category_id,
            is_active=True,
            is_archived=False,
            price_min=None,
            price_max=None,
            sort=sort or ["-created_at"],
            limit=limit,
            offset=offset,
        )
        dto = [ProductOut.model_validate(p, from_attributes=True) for p in items]
        return Page[ProductOut].from_parts(dto, total, limit, offset)
