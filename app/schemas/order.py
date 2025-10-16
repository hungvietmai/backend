from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.db.enums import PaymentMethodEnum

# --- Checkout ---
class ShippingIn(BaseModel):
    full_name: str = Field(max_length=255)
    mobile_num: str = Field(max_length=20)
    detail_address: str = Field(max_length=500)
    province_name: Optional[str] = Field(default=None, max_length=100)
    district_name: Optional[str] = Field(default=None, max_length=100)
    ward_name: Optional[str] = Field(default=None, max_length=100)
    zip_code: Optional[str] = Field(default=None, max_length=20)

class CheckoutIn(BaseModel):
    shipping: ShippingIn
    payment_method: PaymentMethodEnum = PaymentMethodEnum.cod
    pay_now: bool = False                       # simulate instant capture
    shipping_fee_cents: int = Field(default=0, ge=0)
    model_config = ConfigDict(extra="forbid")

class OrderOut(BaseModel):
    id: int
    order_number: str
    status: str
    subtotal_cents: int
    shipping_fee_cents: int
    discount_cents: int
    total_cents: int
    currency: str
    model_config = ConfigDict(from_attributes=True)

class OrderItemOut(BaseModel):
    id: int
    order_id: int
    sku: str
    name: str
    color: Optional[str]
    size: Optional[str]
    qty: int
    unit_price_cents: int
    line_total_cents: int
    model_config = ConfigDict(from_attributes=True)

class OrderDetailOut(OrderOut):
    items: List[OrderItemOut] = []
    model_config = ConfigDict(from_attributes=True)
