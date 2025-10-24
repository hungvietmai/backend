# app/services/admin/review_service.py
from __future__ import annotations
from typing import cast
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.repositories.review_repo import ReviewRepository
from app.exceptions import NotFound


class AdminReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.reviews = ReviewRepository(db)

    def set_published(self, review_id: int, is_published: bool):
        r = self.reviews.get(review_id)
        if not r:
            raise NotFound("Review not found")

        r = self.reviews.update(r, {"is_published": is_published})
        self.db.commit()
        self.db.refresh(r)
        return r

    def soft_delete(self, review_id: int) -> None:
        r = self.reviews.get(review_id)
        if not r:
            return
        # repo helper sets deleted_at to now (UTC)
        self.reviews.soft_delete(r)
        self.db.commit()

    # Optional: restore a soft-deleted review
    def restore(self, review_id: int):
        r = self.reviews.get(review_id)
        if not r:
            raise NotFound("Review not found")
        r = self.reviews.update(r, {"deleted_at": cast("datetime | None", None)})
        self.db.commit()
        self.db.refresh(r)
        return r
