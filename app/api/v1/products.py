# app/api/v1/products.py
from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.schemas.page import Page
from app.schemas.product import (
    ProductOut, VariantOut, ImageOut
)
from app.schemas.review import ReviewCreate, ReviewOut
from app.services.product_service import ProductService
from app.services.review_service import ReviewService

router = APIRouter(prefix="/products", tags=["products"])

@router.get("", response_model=Page[ProductOut])
def list_products(
    q: str | None = Query(None),
    brand_id: int | None = Query(None),
    category_id: int | None = Query(None),
    is_active: bool | None = Query(None),
    is_archived: bool | None = Query(None),
    price_min: int | None = Query(None, ge=0),
    price_max: int | None = Query(None, ge=0),
    sort: List[str] = Query(["-created_at"]),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return ProductService(db).list_products_page(
        q=q, brand_id=brand_id, category_id=category_id,
        is_active=is_active, is_archived=is_archived,
        price_min=price_min, price_max=price_max,
        sort=sort, limit=limit, offset=offset,
    )

@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return ProductService(db).get_product(product_id)

@router.get("/{product_id}/variants", response_model=List[VariantOut])
def list_variants(product_id: int, db: Session = Depends(get_db)):
    return ProductService(db).list_variants(product_id)

@router.get("/{product_id}/images", response_model=List[ImageOut])
def list_images(product_id: int, db: Session = Depends(get_db)):
    return ProductService(db).list_images(product_id)


@router.get("/{product_id}/reviews", response_model=Page[ReviewOut])
def list_product_reviews(
    product_id: int,
    rating_min: int | None = Query(None, ge=1, le=5),
    rating_max: int | None = Query(None, ge=1, le=5),
    sort: list[str] = Query(["-created_at"], description="fields: created_at, rating"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return ReviewService(db).list_product_reviews_page(
        product_id,
        rating_min=rating_min, rating_max=rating_max,
        sort=sort, limit=limit, offset=offset,
    )

@router.post("/{product_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def add_review_for_product(
    product_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
):
    return ReviewService(db).add_review(product_id, payload)