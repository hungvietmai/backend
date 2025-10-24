# app/services/review_service.py
from __future__ import annotations
from sqlalchemy.orm import Session

from app.repositories.review_repo import ReviewRepository
from app.schemas.page import Page
from app.schemas.review import ReviewOut, ReviewCreate, ReviewUpdate
from app.exceptions import NotFound, BadRequest
from app.models.catalog import Product  # to validate product existence


class ReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReviewRepository(db)

    # -------- Public listing for a product --------
    def list_product_reviews_page(
        self,
        product_id: int,
        *,
        rating_min: int | None,
        rating_max: int | None,
        sort: list[str],
        limit: int,
        offset: int,
    ) -> Page[ReviewOut]:
        items, total = self.repo.list_paged_public_for_product(
            product_id, rating_min=rating_min, rating_max=rating_max,
            sort=sort or ["-created_at"], limit=limit, offset=offset
        )
        dto = [ReviewOut.model_validate(r, from_attributes=True) for r in items]
        return Page[ReviewOut].from_parts(dto, total, limit, offset)

    # -------- My reviews listing --------
    def list_my_reviews_page(
        self,
        user_id: int,
        *,
        product_id: int | None,
        sort: list[str],
        limit: int,
        offset: int,
    ) -> Page[ReviewOut]:
        items, total = self.repo.list_paged_for_user(
            user_id, product_id=product_id, sort=sort or ["-created_at"], limit=limit, offset=offset
        )
        dto = [ReviewOut.model_validate(r, from_attributes=True) for r in items]
        return Page[ReviewOut].from_parts(dto, total, limit, offset)

    # -------- Create / Update / Delete --------
    def add_review(self, product_id: int, payload: ReviewCreate) -> ReviewOut:
        # Ensure product exists
        if not self.db.get(Product, product_id):
            raise NotFound("Product not found")

        # Enforce one review per user per product (unique constraint)
        existing = self.repo.get_by_user_and_product(payload.user_id, product_id)
        if existing:
            raise BadRequest("You have already reviewed this product")

        data = payload.model_dump()
        data.update({"user_id": payload.user_id, "product_id": product_id})

        row = self.repo.create(data)
        self.db.commit()

        self.db.refresh(row)
        return ReviewOut.model_validate(row, from_attributes=True)

    def update_review(self, review_id: int, payload: ReviewUpdate) -> ReviewOut:
        row = self.repo.get(review_id)
        if not row or row.deleted_at is not None:
            raise NotFound("Review not found")

        changes = {k: v for k, v in payload.model_dump().items() if v is not None}
        if not changes:
            return ReviewOut.model_validate(row, from_attributes=True)

        row = self.repo.update(row, changes)
        self.db.commit()

        self.db.refresh(row)
        return ReviewOut.model_validate(row, from_attributes=True)

    def delete_review(self, user_id: int, review_id: int) -> None:
        row = self.repo.get(review_id)
        if not row or row.deleted_at is not None:
            raise NotFound("Review not found")
        if row.user_id != user_id:
            raise BadRequest("You can only delete your own review")

        self.repo.soft_delete(row)
        self.db.commit()
