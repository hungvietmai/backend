from __future__ import annotations
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field, ConfigDict

from app.db.enums import ReturnStatusEnum


class ReturnCreate(BaseModel):
    order_id: int
    reason: str | None = None

class ReturnItemCreate(BaseModel):
    order_item_id: int
    qty: int = Field(..., gt=0)

class ReturnItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    return_id: int
    order_item_id: int
    qty: int
    created_at: datetime
    updated_at: datetime

class ReturnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    status: ReturnStatusEnum
    reason: str | None = None
    created_at: datetime
    updated_at: datetime

    # Optional, filled if you return the relationship from service
    items: List[ReturnItemOut] = []

class ReturnDecisionIn(BaseModel):
    approve: bool
    reason: str | None = None

class ReturnReceiveIn(BaseModel):
    note: str | None = None

class ReturnRefundIn(BaseModel):
    reason: str | None = None