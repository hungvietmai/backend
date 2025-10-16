# app/api/v1/admin/products.py
from __future__ import annotations
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductOut,
    VariantCreate, VariantUpdate, VariantOut,
    ImageCreate, ImageUpdate, ImageOut,
)
from app.services.product_service import ProductService

router = APIRouter(
    prefix="/admin/products",
    tags=["admin:products"],
    dependencies=[Depends(require_admin)],
)

# Products
@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    return ProductService(db).create_product(payload)

@router.patch("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    return ProductService(db).update_product(product_id, payload)

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, hard: bool = False, db: Session = Depends(get_db)):
    ProductService(db).delete_product(product_id, hard=hard)
    return

# Variants
@router.post("/{product_id}/variants", response_model=VariantOut, status_code=status.HTTP_201_CREATED)
def add_variant(product_id: int, payload: VariantCreate, db: Session = Depends(get_db)):
    return ProductService(db).add_variant(product_id, payload)

@router.patch("/variants/{variant_id}", response_model=VariantOut)
def update_variant(variant_id: int, payload: VariantUpdate, db: Session = Depends(get_db)):
    return ProductService(db).update_variant(variant_id, payload)

@router.delete("/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(variant_id: int, db: Session = Depends(get_db)):
    ProductService(db).delete_variant(variant_id)
    return

# Images
@router.post("/{product_id}/images", response_model=ImageOut, status_code=status.HTTP_201_CREATED)
def add_image(product_id: int, payload: ImageCreate, db: Session = Depends(get_db)):
    return ProductService(db).add_image(product_id, payload)

@router.patch("/images/{image_id}", response_model=ImageOut)
def update_image(image_id: int, payload: ImageUpdate, db: Session = Depends(get_db)):
    return ProductService(db).update_image(image_id, payload)

@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(image_id: int, db: Session = Depends(get_db)):
    ProductService(db).delete_image(image_id)
    return
