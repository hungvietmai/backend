from __future__ import annotations
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound=BaseModel)

class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int
    next_offset: Optional[int] = None
    prev_offset: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_parts(cls, items: list[T], total: int, limit: int, offset: int) -> "Page[T]":
        return cls(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            next_offset=(offset + limit) if (offset + limit) < total else None,
            prev_offset=(max(offset - limit, 0) if offset > 0 else None),
        )
