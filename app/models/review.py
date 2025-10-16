# app/models/review.py
from __future__ import annotations

from typing import Optional

from sqlalchemy import (
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, SoftDeleteMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.catalog import Product
    from app.models.auth import User


class Review(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    body: Mapped[Optional[str]] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    product: Mapped["Product"] = relationship(back_populates="reviews")
    user: Mapped[Optional["User"]] = relationship(back_populates="reviews")

    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_review_rating_1_5"),
        UniqueConstraint("product_id", "user_id", name="uq_review_user_once"),
        Index("ix_reviews_product_created_at", "product_id", "created_at"),
        Index("ix_reviews_user_created_at", "user_id", "created_at"),
        Index("ix_reviews_product_published", "product_id", "is_published"),
    )

    def __repr__(self) -> str:
        return (
            f"<Review id={self.id} product_id={self.product_id} "
            f"user_id={self.user_id} rating={self.rating} published={self.is_published}>"
        )
