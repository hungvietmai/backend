# app/services/product_service.py
from __future__ import annotations
from typing import Sequence
from sqlalchemy.orm import Session

from app.repositories.product_repo import ProductRepository
from app.schemas.page import Page
from app.schemas.product import (
    ImageOut, ProductCreate, ProductOut, ProductUpdate,
    VariantCreate, VariantUpdate, ImageCreate, ImageUpdate,
)
from app.models.catalog import Product, ProductVariant, ProductImage
from app.exceptions import NotFound, Conflict, BadRequest
from app.utils.strings import slugify_unique


class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProductRepository(db)

    # ---------- Product ----------
    def create_product(self, payload: ProductCreate) -> Product:
        # slug uniqueness via repo.get_by_slug
        slug_source = payload.slug or payload.name
        slug = slugify_unique(self.repo.get_by_slug, slug_source)

        data = {
            "name": payload.name,
            "slug": slug,
            "brand_id": payload.brand_id,
            "description": payload.description,
            "base_price_cents": payload.base_price_cents,
            "currency": payload.currency,
            "is_active": payload.is_active,
            "is_archived": payload.is_archived,
        }

        p = self.repo.create(data)
        # If your repo exposes category assignment (e.g., set_categories),
        # call it here. Otherwise, skip or implement in repo.
        if getattr(payload, "category_ids", None):
            # Optional: only if ProductRepository implements this.
            set_cats = getattr(self.repo, "set_categories", None)
            if callable(set_cats):
                set_cats(p.id, payload.category_ids)

        self.db.commit()
        self.db.refresh(p)
        return p

    def update_product(self, product_id: int, payload: ProductUpdate) -> Product:
        p = self.repo.get(product_id)
        if not p:
            raise NotFound(detail="Product not found")

        updates: dict = {}
        if payload.name is not None:
            updates["name"] = payload.name

        if payload.slug is not None:
            existing = self.repo.get_by_slug(payload.slug)
            if existing and existing.id != p.id:
                raise Conflict(detail="Slug already in use", errors={"slug": ["taken"]})
            updates["slug"] = payload.slug

        if payload.brand_id is not None:        updates["brand_id"] = payload.brand_id
        if payload.description is not None:     updates["description"] = payload.description
        if payload.base_price_cents is not None: updates["base_price_cents"] = payload.base_price_cents
        if payload.currency is not None:        updates["currency"] = payload.currency
        if payload.is_active is not None:       updates["is_active"] = payload.is_active
        if payload.is_archived is not None:     updates["is_archived"] = payload.is_archived

        if updates:
            p = self.repo.update(p, updates)
        if payload.category_ids is not None:
            set_cats = getattr(self.repo, "set_categories", None)
            if callable(set_cats):
                set_cats(p.id, payload.category_ids)

        self.db.commit()
        self.db.refresh(p)
        return p

    def get_product(self, product_id: int) -> Product:
        p = self.repo.get(product_id)
        if not p:
            raise NotFound(detail="Product not found")
        return p

    def list_products_page(self, **kwargs) -> Page[ProductOut]:
        items, total = self.repo.list_paged(**kwargs)
        dto = [ProductOut.model_validate(p, from_attributes=True) for p in items]
        return Page[ProductOut].from_parts(
            dto, total, kwargs.get("limit", 50), kwargs.get("offset", 0)
        )

    def list_images(self, product_id: int) -> list[ImageOut]:
        imgs: Sequence[ProductImage] = self.repo.list_images(product_id)
        return [ImageOut.model_validate(i, from_attributes=True) for i in imgs]

    def delete_product(self, product_id: int, *, hard: bool = False) -> None:
        p = self.repo.get(product_id)
        if not p:
            raise NotFound(detail="Product not found")

        if hard:
            # new repo has only `delete(row)` → perform hard delete there
            self.repo.delete(p)
        else:
            # soft/archive via flag; actual SoftDelete can be added if desired
            self.repo.update(p, {"is_archived": True})

        self.db.commit()

    # ---------- Variants ----------
    def add_variant(self, product_id: int, payload: VariantCreate) -> ProductVariant:
        if not self.repo.get(product_id):
            raise NotFound(detail="Product not found")

        data = {
            "sku": payload.sku,
            "color": payload.color,
            "size": payload.size,
            "stock_qty": payload.stock_qty,
            "price_cents": payload.price_cents,
            "image_url": payload.image_url,
        }

        try:
            v = self.repo.create_variant(product_id, data)
            self.db.commit()
            self.db.refresh(v)
            return v
        except Exception as e:
            raise BadRequest(detail="Could not create variant") from e

    def update_variant(self, variant_id: int, payload: VariantUpdate) -> ProductVariant:
        v = self.repo.get_variant(variant_id)
        if not v:
            raise NotFound(detail="Variant not found")

        data: dict = {}
        if payload.color is not None:      data["color"] = payload.color
        if payload.size is not None:       data["size"] = payload.size
        if payload.stock_qty is not None:  data["stock_qty"] = payload.stock_qty
        if payload.price_cents is not None: data["price_cents"] = payload.price_cents
        if payload.image_url is not None:  data["image_url"] = payload.image_url

        v = self.repo.update_variant(v, data)
        self.db.commit()
        self.db.refresh(v)
        return v

    def list_variants(self, product_id: int) -> Sequence[ProductVariant]:
        if not self.repo.get(product_id):
            raise NotFound(detail="Product not found")
        return self.repo.list_variants(product_id)

    def delete_variant(self, variant_id: int) -> None:
        v = self.repo.get_variant(variant_id)
        if not v:
            return
        self.repo.delete_variant(v)
        self.db.commit()

    # ---------- Images ----------
    def add_image(self, product_id: int, payload: ImageCreate) -> ProductImage:
        if not self.repo.get(product_id):
            raise NotFound(detail="Product not found")

        data = {"url": payload.url, "is_primary": payload.is_primary, "sort_order": payload.sort_order}

        img = self.repo.add_image(product_id, data)
        if payload.is_primary:
            # demote others
            for other in self.repo.list_images(product_id):
                if other.id != img.id and other.is_primary:
                    self.repo.update_image(other, {"is_primary": False})

        self.db.commit()
        self.db.refresh(img)
        return img

    def update_image(self, image_id: int, payload: ImageUpdate) -> ProductImage:
        img = self.repo.get_image(image_id)
        if not img:
            raise NotFound(detail="Image not found")

        data: dict = {}
        if payload.is_primary is not None: data["is_primary"] = payload.is_primary
        if payload.sort_order is not None: data["sort_order"] = payload.sort_order

        img = self.repo.update_image(img, data)
        if data.get("is_primary"):
            for other in self.repo.list_images(img.product_id):
                if other.id != img.id and other.is_primary:
                    self.repo.update_image(other, {"is_primary": False})

        self.db.commit()
        self.db.refresh(img)
        return img

    def delete_image(self, image_id: int) -> None:
        img = self.repo.get_image(image_id)
        if not img:
            return
        self.repo.delete_image(img)
        self.db.commit()
