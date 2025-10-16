from __future__ import annotations

from typing import Optional

from sqlalchemy import String, Boolean, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.auth import User

class Address(Base, TimestampMixin):
    """
    Shipping/billing address (Vietnam-focused fields).
    Uses a partial unique index so each user can have at most one default address.
    """
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mobile_num: Mapped[str] = mapped_column(String(20), nullable=False)

    zip_code: Mapped[Optional[str]] = mapped_column(String(20))
    detail_address: Mapped[str] = mapped_column(String(500), nullable=False)

    province_code: Mapped[Optional[str]] = mapped_column(String(20))
    province_name: Mapped[Optional[str]] = mapped_column(String(100))
    district_code: Mapped[Optional[str]] = mapped_column(String(20))
    district_name: Mapped[Optional[str]] = mapped_column(String(100))
    ward_code: Mapped[Optional[str]] = mapped_column(String(20))
    ward_name: Mapped[Optional[str]] = mapped_column(String(100))

    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="addresses")

    # One default address per user (partial unique index):
    __table_args__ = (
        Index(
            "uq_addresses_user_default",
            "user_id",
            unique=True,
            # SQLite dialect filter
            sqlite_where=text("is_default = 1"),
            # PostgreSQL dialect filter
            postgresql_where=text("is_default = TRUE"),
        ),
    )

    def __repr__(self) -> str:  # helpful for logs
        return f"<Address id={self.id} user_id={self.user_id} default={self.is_default}>"
