from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class CartItemIn(BaseModel):
    variant_id: int
    qty: int = Field(ge=1, le=999)
    model_config = ConfigDict(extra="forbid")

class CartItemUpdate(BaseModel):
    qty: int = Field(ge=1, le=999)
    model_config = ConfigDict(extra="forbid")

class CartItemOut(BaseModel):
    id: int
    cart_id: int
    variant_id: int
    qty: int
    unit_price_cents: int
    line_total_cents: int
    model_config = ConfigDict(from_attributes=True)

class CartOut(BaseModel):
    id: int
    user_id: int
    items: List[CartItemOut] = []
    subtotal_cents: int
    model_config = ConfigDict(from_attributes=True)
