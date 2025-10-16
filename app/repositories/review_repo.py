from __future__ import annotations
from typing import Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.common.listing import paginate, safe_order_by, Col, ilike_any
from app.models.review import Review

ALLOWED_SORT: dict[str, Col] = {
    "id": Review.id,
    "created_at": Review.created_at,
    "rating": Review.rating,
}
DEFAULT_SORT = ["-created_at"]


class ReviewRepository:
    """Role-agnostic; services enforce permissions/publishing. No commits here."""
    def __init__(self, db: Session):
        self.db = db

    # ----- Reads -----
    def get(self, review_id: int) -> Optional[Review]:
        return self.db.get(Review, review_id)

    def get_by_user_and_product(self, user_id: int, product_id: int) -> Optional[Review]:
        stmt: Select[tuple[Review]] = select(Review).where(
            Review.user_id == user_id,
            Review.product_id == product_id,
            Review.deleted_at.is_(None),
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_paged_public_for_product(
        self,
        product_id: int,
        *,
        rating_min: int | None,
        rating_max: int | None,
        sort: List[str],
        limit: int,
        offset: int,
    ) -> Tuple[List[Review], int]:
        stmt: Select[tuple[Review]] = select(Review).where(
            Review.product_id == product_id,
            Review.is_published.is_(True),
            Review.deleted_at.is_(None),
        )
        if rating_min is not None:
            stmt = stmt.where(Review.rating >= rating_min)
        if rating_max is not None:
            stmt = stmt.where(Review.rating <= rating_max)

        stmt = stmt.order_by(*safe_order_by(sort, ALLOWED_SORT, DEFAULT_SORT))
        return paginate(self.db, stmt, limit, offset)

    def list_paged_for_user(
        self,
        user_id: int,
        *,
        product_id: int | None,
        sort: List[str],
        limit: int,
        offset: int,
    ) -> Tuple[List[Review], int]:
        stmt: Select[tuple[Review]] = select(Review).where(
            Review.user_id == user_id,
            Review.deleted_at.is_(None),
        )
        if product_id is not None:
            stmt = stmt.where(Review.product_id == product_id)
        stmt = stmt.order_by(*safe_order_by(sort, ALLOWED_SORT, DEFAULT_SORT))
        return paginate(self.db, stmt, limit, offset)

    # ----- Writes (no commits) -----
    def create(self, data: dict) -> Review:
        row = Review(**data)
        self.db.add(row)
        return row

    def update(self, row: Review, data: dict) -> Review:
        for k, v in data.items():
            setattr(row, k, v)
        self.db.add(row)
        return row

    def soft_delete(self, row: Review) -> None:
        setattr(row, "deleted_at", datetime.now(timezone.utc))
        self.db.add(row)
