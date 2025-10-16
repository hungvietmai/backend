from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.schemas.page import Page
from app.schemas.catalog import BrandCreate, BrandOut, BrandUpdate, CategoryCreate, CategoryOut, CategoryUpdate
from app.services.admin.catalog_service import AdminCatalogService

router = APIRouter(prefix="/admin/catalog", tags=["admin:catalog"], dependencies=[Depends(require_admin)])

# Brands
@router.get("/brands", response_model=Page[BrandOut])
def list_brands(q: str | None = Query(None), sort: List[str] = Query(["name"]), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return AdminCatalogService(db).list_brands_page(q=q, sort=sort, limit=limit, offset=offset)

@router.post("/brands", response_model=BrandOut, status_code=status.HTTP_201_CREATED)
def create_brand(payload: BrandCreate, db: Session = Depends(get_db)):
    row = AdminCatalogService(db).create_brand(payload.model_dump())
    return BrandOut.model_validate(row, from_attributes=True)

@router.patch("/brands/{brand_id}", response_model=BrandOut)
def update_brand(brand_id: int, payload: BrandUpdate, db: Session = Depends(get_db)):
    row = AdminCatalogService(db).update_brand(brand_id, payload.model_dump(exclude_none=True))
    return BrandOut.model_validate(row, from_attributes=True)

@router.delete("/brands/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brand(brand_id: int, hard: bool = Query(False), db: Session = Depends(get_db)):
    AdminCatalogService(db).delete_brand(brand_id, hard=hard); return

# Categories
@router.get("/categories", response_model=Page[CategoryOut])
def list_categories(q: str | None = Query(None), parent_id: int | None = Query(None), sort: List[str] = Query(["name"]), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return AdminCatalogService(db).list_categories_page(q=q, parent_id=parent_id, sort=sort, limit=limit, offset=offset)

@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    row = AdminCatalogService(db).create_category(payload.model_dump())
    return CategoryOut.model_validate(row, from_attributes=True)

@router.patch("/categories/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
    row = AdminCatalogService(db).update_category(category_id, payload.model_dump(exclude_none=True))
    return CategoryOut.model_validate(row, from_attributes=True)

@router.patch("/categories/{category_id}/move", response_model=CategoryOut)
def move_category(category_id: int, parent_id: int | None = Query(None), db: Session = Depends(get_db)):
    row = AdminCatalogService(db).move_category(category_id, parent_id)
    return CategoryOut.model_validate(row, from_attributes=True)

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, hard: bool = Query(False), db: Session = Depends(get_db)):
    AdminCatalogService(db).delete_category(category_id, hard=hard); return
