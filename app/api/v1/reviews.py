from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.page import Page
from app.schemas.review import ReviewOut, ReviewUpdate
from app.services.review_service import ReviewService
from app.models.auth import User

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.get("/me", response_model=Page[ReviewOut])
def list_my_reviews(
    product_id: int | None = Query(None),
    sort: list[str] = Query(["-created_at"]),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReviewService(db).list_my_reviews_page(
        current.id, product_id=product_id, sort=sort, limit=limit, offset=offset
    )

@router.patch("/{review_id}", response_model=ReviewOut)
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
):
    return ReviewService(db).update_review(review_id, payload)

@router.delete("/{review_id}", status_code=204)
def delete_review(
    review_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ReviewService(db).delete_review(current.id, review_id)
    return
