from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.page import Page
from app.schemas.catalog import BrandOut, CategoryOut, CategoryNodeOut
from app.schemas.product import ProductOut
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/catalog", tags=["catalog"])

# ---- Brands ----
@router.get("/brands", response_model=Page[BrandOut])
def list_brands(q: str | None = None,
                sort: list[str] = Query(["name"]),
                limit: int = Query(100, ge=1, le=200),
                offset: int = Query(0, ge=0),
                db: Session = Depends(get_db)):
    return CatalogService(db).list_brands_page(q=q, sort=sort, limit=limit, offset=offset)

@router.get("/brands/{brand_id}", response_model=BrandOut)
def get_brand(brand_id: int, db: Session = Depends(get_db)):
    return CatalogService(db).get_brand(brand_id)

@router.get("/brands/{brand_id}/products", response_model=Page[ProductOut])
def list_brand_products(brand_id: int,
                        q: str | None = None,
                        sort: list[str] = Query(["-created_at"]),
                        limit: int = Query(50, ge=1, le=200),
                        offset: int = Query(0, ge=0),
                        db: Session = Depends(get_db)):
    return CatalogService(db).list_products_by_brand_page(brand_id, q=q, sort=sort, limit=limit, offset=offset)

# ---- Categories ----
@router.get("/categories", response_model=Page[CategoryOut])
def list_categories(q: str | None = None,
                    parent_id: int | None = None,
                    sort: list[str] = Query(["name"]),
                    limit: int = Query(200, ge=1, le=500),
                    offset: int = Query(0, ge=0),
                    db: Session = Depends(get_db)):
    return CatalogService(db).list_categories_page(q=q, parent_id=parent_id, sort=sort, limit=limit, offset=offset)

@router.get("/categories/tree", response_model=List[CategoryNodeOut])
def category_tree(db: Session = Depends(get_db)):
    return CatalogService(db).category_tree()

@router.get("/categories/{category_id}", response_model=CategoryOut)
def get_category(category_id: int, db: Session = Depends(get_db)):
    return CatalogService(db).get_category(category_id)

@router.get("/categories/{category_id}/products", response_model=Page[ProductOut])
def list_category_products(category_id: int,
                           q: str | None = None,
                           sort: list[str] = Query(["-created_at"]),
                           limit: int = Query(50, ge=1, le=200),
                           offset: int = Query(0, ge=0),
                           db: Session = Depends(get_db)):
    return CatalogService(db).list_products_by_category_page(category_id, q=q, sort=sort, limit=limit, offset=offset)
