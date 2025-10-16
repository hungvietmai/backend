from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    Adds DB-managed timestamps.
    - created_at: set by the DB on INSERT
    - updated_at: set by the DB on INSERT and updated on UPDATE
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """
    Adds soft-delete support via a nullable deleted_at column and helpers.
    """
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, *, at: Optional[datetime] = None) -> None:
        """Mark the row as deleted without removing it from the DB."""
        self.deleted_at = at or datetime.now(timezone.utc)

    def restore(self) -> None:
        """Undo a soft delete."""
        self.deleted_at = None
