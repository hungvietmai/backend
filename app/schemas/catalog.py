from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

# ---- Read models for users/admin ----
class BrandOut(BaseModel):
    id: int
    name: str
    slug: str
    created_at: str
    model_config = ConfigDict(from_attributes=True)

class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    parent_id: Optional[int] = None
    created_at: str
    model_config = ConfigDict(from_attributes=True)

class CategoryNodeOut(BaseModel):
    id: int
    name: str
    slug: str
    parent_id: Optional[int] = None
    children: List["CategoryNodeOut"] = []
    model_config = ConfigDict(from_attributes=True)

# ---- Write payloads (admin) ----
class BrandIn(BaseModel):
    name: str = Field(max_length=120)
    slug: str = Field(max_length=160)

class CategoryIn(BaseModel):
    name: str = Field(max_length=120)
    slug: str = Field(max_length=160)
    parent_id: Optional[int] = None

class BrandCreate(BaseModel):
    name: str
    slug: str | None = None

class BrandUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None

class CategoryCreate(BaseModel):
    name: str
    slug: str | None = None
    parent_id: int | None = None

class CategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    parent_id: int | None = None