from __future__ import annotations
from typing import Optional, Sequence, Tuple, List
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.common.listing import paginate, safe_order_by, Col
from app.models.payment import Payment
from app.db.enums import PaymentStatusEnum, PaymentMethodEnum

ALLOWED_SORT: dict[str, Col] = {
    "id": Payment.id,
    "created_at": Payment.created_at,
    "amount": Payment.amount_cents,
    "status": Payment.status,
    "method": Payment.method,
    "order_id": Payment.order_id,
}
DEFAULT_SORT = ["-created_at"]

class PaymentRepository:
    def __init__(self, db: Session): self.db = db

    # --- reads ---
    def get(self, payment_id: int) -> Optional[Payment]:
        return self.db.get(Payment, payment_id)

    def list_for_order(self, order_id: int) -> Sequence[Payment]:
        stmt = select(Payment).where(Payment.order_id == order_id).order_by(Payment.created_at.asc())
        return self.db.execute(stmt).scalars().all()

    def total_paid_for_order(self, order_id: int) -> int:
        stmt = select(func.coalesce(func.sum(Payment.amount_cents), 0)).where(
            Payment.order_id == order_id, Payment.status == PaymentStatusEnum.paid
        )
        return int(self.db.execute(stmt).scalar_one())

    def list_paged(
        self,
        *,
        order_id: int | None,
        status: list[str] | None,
        method: list[str] | None,
        sort: List[str],
        limit: int,
        offset: int,
    ) -> Tuple[Sequence[Payment], int]:
        stmt: Select[tuple[Payment]] = select(Payment)
        conds = []
        if order_id is not None: conds.append(Payment.order_id == order_id)
        if status: conds.append(Payment.status.in_(status))
        if method: conds.append(Payment.method.in_(method))
        if conds: stmt = stmt.where(and_(*conds))
        stmt = stmt.order_by(*safe_order_by(sort, ALLOWED_SORT, DEFAULT_SORT))
        return paginate(self.db, stmt, limit, offset)

    # --- writes (no commits) ---
    def create(self, order_id: int, *, amount_cents: int, status: PaymentStatusEnum, method: PaymentMethodEnum, transaction_ref: str | None = None) -> Payment:
        row = Payment(order_id=order_id, amount_cents=amount_cents, status=status, method=method, transaction_ref=transaction_ref)
        self.db.add(row); return row

    def save(self, row: Payment) -> None:
        self.db.add(row)
