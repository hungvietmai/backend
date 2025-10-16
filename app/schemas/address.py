from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AddressBase(BaseModel):
    full_name: str
    mobile_num: str
    detail_address: str

    province_code: str | None = None
    province_name: str | None = None
    district_code: str | None = None
    district_name: str | None = None
    ward_code: str | None = None
    ward_name: str | None = None

    zip_code: str | None = None
    note: str | None = None

class AddressCreate(AddressBase):
    # service will force is_default=True for the first address
    is_default: bool = False

class AddressUpdate(BaseModel):
    full_name: str | None = None
    mobile_num: str | None = None
    detail_address: str | None = None

    province_code: str | None = None
    province_name: str | None = None
    district_code: str | None = None
    district_name: str | None = None
    ward_code: str | None = None
    ward_name: str | None = None

    zip_code: str | None = None
    note: str | None = None
    # True means “make this the default”. False is ignored by the service to avoid zero-default state.
    is_default: bool | None = None

class AddressOut(AddressBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    is_default: bool
    created_at: datetime
    updated_at: datetime
