from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.page import Page
from app.schemas.returns import ReturnOut, ReturnCreate, ReturnItemCreate, ReturnItemOut
from app.services.returns_service import ReturnsService
from app.models.auth import User

router = APIRouter(prefix="/returns", tags=["returns"])

@router.get("", response_model=Page[ReturnOut])
def list_my_returns(
    status: List[str] | None = Query(None),
    sort: List[str] = Query(["-created_at"]),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReturnsService(db).list_my_page(current.id, status=status, sort=sort, limit=limit, offset=offset)

@router.get("/{return_id}", response_model=ReturnOut)
def get_return(return_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = ReturnsService(db).get_for_user(current.id, return_id)
    return ReturnOut.model_validate(r, from_attributes=True)

@router.post("", response_model=ReturnOut, status_code=status.HTTP_201_CREATED)
def create_return(payload: ReturnCreate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = ReturnsService(db).create(current.id, payload.order_id, payload.reason)
    return ReturnOut.model_validate(r, from_attributes=True)

@router.post("/{return_id}/items", response_model=ReturnItemOut, status_code=status.HTTP_201_CREATED)
def add_return_item(return_id: int, payload: ReturnItemCreate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = ReturnsService(db).add_item(current.id, return_id, payload.order_item_id, payload.qty)
    return ReturnItemOut.model_validate(row, from_attributes=True)

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_return_item(item_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ReturnsService(db).remove_item(current.id, item_id)
    return
