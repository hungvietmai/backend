from __future__ import annotations

from typing import Optional, List

from sqlalchemy import String, Boolean
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, SoftDeleteMixin
from app.db.enums import UserRoleEnum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.cart import Cart
    from app.models.address import Address
    from app.models.order import Order
    from app.models.review import Review

class User(Base, TimestampMixin, SoftDeleteMixin):
    """
    Core user entity.
    - Soft-deletable (deleted_at) to preserve order/review history.
    - `orders.user_id` uses SET NULL so financial records remain if a user is deleted.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRoleEnum] = mapped_column(
        SAEnum(UserRoleEnum, name="user_role", native_enum=False, validate_strings=True),
        default=UserRoleEnum.customer,
        index=True,
        nullable=False,
    )

    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships (use string targets to avoid cross-file imports)
    addresses: Mapped[List["Address"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    carts: Mapped[List["Cart"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    orders: Mapped[List["Order"]] = relationship(
        back_populates="user",
    )
    reviews: Mapped[List["Review"]] = relationship(
        back_populates="user",
    )

    # Helpful for debugging
    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role} active={self.is_active} deleted={self.deleted_at is not None}>"
