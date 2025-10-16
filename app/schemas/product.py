from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

# ---------- Product ----------
class ProductBase(BaseModel):
    name: str = Field(max_length=255)
    slug: Optional[str] = Field(default=None, max_length=255)
    brand_id: Optional[int] = None
    description: Optional[str] = None
    base_price_cents: int = Field(ge=0)
    currency: str = Field(default="VND", min_length=3, max_length=3)
    is_active: bool = True
    is_archived: bool = False

class ProductCreate(ProductBase):
    category_ids: List[int] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    slug: Optional[str] = Field(default=None, max_length=255)
    brand_id: Optional[int] = None
    description: Optional[str] = None
    base_price_cents: Optional[int] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    is_active: Optional[bool] = None
    is_archived: Optional[bool] = None
    category_ids: Optional[List[int]] = None
    model_config = ConfigDict(extra="forbid")

class ProductOut(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ---------- Variants ----------
class VariantCreate(BaseModel):
    sku: str = Field(max_length=64)
    color: Optional[str] = Field(default=None, max_length=64)
    size: Optional[str]  = Field(default=None, max_length=32)
    stock_qty: int = Field(ge=0, default=0)
    price_cents: Optional[int] = Field(default=None, ge=0)
    image_url: Optional[str] = Field(default=None, max_length=500)
    model_config = ConfigDict(extra="forbid")

class VariantUpdate(BaseModel):
    color: Optional[str] = Field(default=None, max_length=64)
    size: Optional[str]  = Field(default=None, max_length=32)
    stock_qty: Optional[int] = Field(default=None, ge=0)
    price_cents: Optional[int] = Field(default=None, ge=0)
    image_url: Optional[str] = Field(default=None, max_length=500)
    model_config = ConfigDict(extra="forbid")

class VariantOut(BaseModel):
    id: int
    product_id: int
    sku: str
    color: Optional[str]
    size: Optional[str]
    stock_qty: int
    price_cents: Optional[int]
    image_url: Optional[str]
    model_config = ConfigDict(from_attributes=True)

# ---------- Images ----------
class ImageCreate(BaseModel):
    url: str = Field(max_length=500)
    is_primary: bool = False
    sort_order: int = 0
    model_config = ConfigDict(extra="forbid")

class ImageUpdate(BaseModel):
    is_primary: Optional[bool] = None
    sort_order: Optional[int] = None
    model_config = ConfigDict(extra="forbid")

class ImageOut(BaseModel):
    id: int
    product_id: int
    url: str
    is_primary: bool
    sort_order: int
    model_config = ConfigDict(from_attributes=True)
