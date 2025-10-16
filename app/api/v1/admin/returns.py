# app/api/v1/admin/returns.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.services.admin.returns_service import AdminReturnsService
from app.schemas.returns import (
    ReturnOut, ReturnDecisionIn, ReturnReceiveIn, ReturnRefundIn
)

router = APIRouter(prefix="/admin/returns", tags=["admin:returns"], dependencies=[Depends(require_admin)])

@router.post("/{return_id}/decision", response_model=ReturnOut)
def decide(return_id: int, payload: ReturnDecisionIn, db: Session = Depends(get_db)):
    svc = AdminReturnsService(db)
    r = svc.decide(return_id, approve=payload.approve, reason=payload.reason)
    return ReturnOut.model_validate(r, from_attributes=True)

@router.post("/{return_id}/received", response_model=ReturnOut)
def mark_received(return_id: int, payload: ReturnReceiveIn, db: Session = Depends(get_db)):
    r = AdminReturnsService(db).mark_received(return_id, note=payload.note)
    return ReturnOut.model_validate(r, from_attributes=True)

@router.post("/{return_id}/refund", response_model=ReturnOut)
def refund(return_id: int, payload: ReturnRefundIn, db: Session = Depends(get_db)):
    r = AdminReturnsService(db).refund(return_id)
    return ReturnOut.model_validate(r, from_attributes=True)

@router.post("/{return_id}/close", response_model=ReturnOut)
def close(return_id: int, db: Session = Depends(get_db)):
    r = AdminReturnsService(db).close(return_id)
    return ReturnOut.model_validate(r, from_attributes=True)
