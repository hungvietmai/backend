from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.db.enums import InventoryMovementType

class ManualAdjustIn(BaseModel):
    variant_id: int
    qty_delta: int = Field(..., description="positive to add, negative to remove")
    note: str | None = None

class InventoryMovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    variant_id: int
    order_id: int | None = None
    qty_delta: int
    reason: InventoryMovementType
    note: str | None = None
    created_at: datetime
