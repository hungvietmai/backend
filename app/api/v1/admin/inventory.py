# app/api/routes/admin_inventory.py
from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.schemas.inventory import ManualAdjustIn, InventoryMovementOut
from app.schemas.page import Page
from app.db.enums import InventoryMovementType
from app.services.admin.inventory_service import AdminInventoryService

router = APIRouter(
    prefix="/admin/inventory",
    tags=["admin:inventory"],
    dependencies=[Depends(require_admin)],
)

@router.get("/movements", response_model=Page[InventoryMovementOut])
def list_movements(
    variant_id: int | None = Query(None),
    order_id: int | None = Query(None),
    reason: InventoryMovementType | None = Query(None),
    sort: List[str] = Query(["-created_at"]),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    items, total, limit, offset = AdminInventoryService(db).list_movements_page(
        variant_id=variant_id, order_id=order_id, reason=reason, sort=sort, limit=limit, offset=offset
    )
    # map ORM rows to DTOs
    dto_items = [InventoryMovementOut.model_validate(o) for o in items]
    return Page[InventoryMovementOut].from_parts(dto_items, total, limit, offset)

@router.post("/adjust", response_model=InventoryMovementOut, status_code=status.HTTP_201_CREATED)
def manual_adjust(payload: ManualAdjustIn, db: Session = Depends(get_db)):
    obj = AdminInventoryService(db).manual_adjust(
        variant_id=payload.variant_id, qty_delta=payload.qty_delta, note=payload.note
    )
    return InventoryMovementOut.model_validate(obj)
