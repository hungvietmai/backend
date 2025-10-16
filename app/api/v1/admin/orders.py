# app/api/v1/admin/orders.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.schemas.order import OrderOut
from app.schemas.page import Page
from app.services.admin.order_service import AdminOrderService
from app.db.enums import ShipmentStatusEnum, PaymentMethodEnum
from app.services.order_service import OrderService

router = APIRouter(prefix="/admin/orders", tags=["admin:orders"], dependencies=[Depends(require_admin)])

@router.get("", response_model=Page[OrderOut])
def list_orders(
    user_id: int | None = None,
    status: list[str] | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
    min_total: int | None = None,
    max_total: int | None = None,
    sort: list[str] = ["-created_at"],
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    svc = AdminOrderService(db)
    return svc.list_page(
        user_id=user_id, status=status, created_from=created_from, created_to=created_to,
        min_total=min_total, max_total=max_total, sort=sort, limit=limit, offset=offset
    )

@router.post("/{order_id}/mark-paid")
def mark_paid(order_id: int, method: PaymentMethodEnum = PaymentMethodEnum.momo, db: Session = Depends(get_db)):
    return AdminOrderService(db).mark_paid(order_id, method)

@router.post("/{order_id}/cancel")
def cancel(order_id: int, db: Session = Depends(get_db)):
    return AdminOrderService(db).cancel(order_id)

@router.post("/{order_id}/shipment")
def create_shipment(order_id: int, carrier: str | None = None, tracking: str | None = None, db: Session = Depends(get_db)):
    return AdminOrderService(db).create_shipment(order_id, carrier, tracking)

@router.patch("/{order_id}/shipment")
def update_shipment(
    order_id: int,
    status: ShipmentStatusEnum,
    carrier: str | None = None,
    tracking: str | None = None,
    shipped_at: str | None = None,
    delivered_at: str | None = None,
    db: Session = Depends(get_db),
):
    return AdminOrderService(db).update_shipment(order_id, status=status, carrier=carrier, tracking=tracking, shipped_at_iso=shipped_at, delivered_at_iso=delivered_at)

@router.post("/{order_id}/refund")
def refund(order_id: int, reason: str | None = None, db: Session = Depends(get_db)):
    return AdminOrderService(db).refund_order(order_id, reason)

@router.post("/{order_id}/fulfill", response_model=OrderOut, dependencies=[Depends(require_admin)])
def mark_fulfilled(order_id: int, db: Session = Depends(get_db)):
    o = OrderService(db).mark_fulfilled(order_id)
    return o
