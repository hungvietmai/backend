from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.order import CheckoutIn, OrderOut, OrderDetailOut
from app.schemas.common import Problem
from app.services.order_service import OrderService
from app.db.enums import PaymentMethodEnum
from app.models.auth import User

router = APIRouter(prefix="/orders", tags=["orders"])

@router.get("", response_model=List[OrderOut])
def list_my_orders(
    status: Optional[List[str]] = Query(None, description="Repeat param, e.g. ?status=pending&status=paid"),
    created_from: datetime | None = Query(None),
    created_to: datetime | None = Query(None),
    min_total: int | None = Query(None, ge=0),
    max_total: int | None = Query(None, ge=0),
    sort: List[str] = Query(["-created_at"], description="fields: id, order_number, created_at, status, total, paid_at"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrderService(db).list_my_orders_page(
        current.id, status=status, created_from=created_from, created_to=created_to,
        min_total=min_total, max_total=max_total, sort=sort, limit=limit, offset=offset,
    )

@router.get("/{order_id}", response_model=OrderDetailOut, responses={404: {"model": Problem}})
def get_order(order_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    o = OrderService(db).get_for_user(current.id, order_id)
    return OrderDetailOut.model_validate(o, from_attributes=True)

@router.post(
    "/checkout",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": Problem}},
)
def checkout(payload: CheckoutIn, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    o = OrderService(db).checkout(
        user_id=current.id,
        shipping=payload.shipping.model_dump(),
        payment_method=payload.payment_method,
        pay_now=payload.pay_now,
        shipping_fee_cents=payload.shipping_fee_cents,
    )
    return o

@router.post("/{order_id}/pay", response_model=OrderOut, responses={400: {"model": Problem}})
def pay(order_id: int, method: PaymentMethodEnum = PaymentMethodEnum.momo, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    o = OrderService(db).pay(current.id, order_id, method)
    return o

@router.post("/{order_id}/cancel", response_model=OrderOut, responses={400: {"model": Problem}})
def cancel(order_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    o = OrderService(db).cancel(current.id, order_id)
    return o