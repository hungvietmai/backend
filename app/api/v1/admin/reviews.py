from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.schemas.review import ReviewModerateIn
from app.services.admin.review_service import AdminReviewService

router = APIRouter(prefix="/admin/reviews", tags=["admin:reviews"], dependencies=[Depends(require_admin)])

@router.post("/{review_id}/moderate")
def moderate(review_id: int, payload: ReviewModerateIn, db: Session = Depends(get_db)):
    return AdminReviewService(db).set_published(review_id, payload.is_published)

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, db: Session = Depends(get_db)):
    AdminReviewService(db).soft_delete(review_id); return
