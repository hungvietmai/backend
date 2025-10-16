from __future__ import annotations
from typing import Any, Iterable, Mapping, Sequence, TypeVar, cast
from sqlalchemy import select, func, or_
from sqlalchemy.sql import Select, ColumnElement
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute

T = TypeVar("T")

Columnish = ColumnElement[Any] | InstrumentedAttribute[Any]


def paginate(db: Session, base_stmt: Select[tuple[T]], limit: int, offset: int) -> tuple[list[T], int]:
    """
    Count over the filtered base statement, then fetch the page.
    Works with joins because we count a subquery of the filtered statement.
    """
    id_only = base_stmt.with_only_columns(1).order_by(None).subquery()
    total = db.scalar(select(func.count()).select_from(id_only)) or 0

    result = db.execute(base_stmt.limit(limit).offset(offset))
    # .scalars().all() is a real list at runtime; cast for the type checker.
    items = cast(list[T], result.scalars().all())
    return items, total

def safe_order_by(sort: Sequence[str], allowed: Mapping[str, ColumnElement], default: Sequence[str]) -> list[ColumnElement]:
    """
    Convert strings like ["-created_at", "name"] into ColumnElements using an allowlist.
    Unknown fields are ignored. Direction: '-' = desc, otherwise asc.
    Always add a deterministic id tiebreaker if available and not already present.
    """
    def resolve_one(s: str) -> ColumnElement | None:
        direction = "asc"
        field = s
        if s.startswith("-"):
            direction = "desc"
            field = s[1:]
        col = allowed.get(field)
        if col is None:
            return None
        return col.desc() if direction == "desc" else col.asc()

    order_by: list[ColumnElement] = []
    for s in (sort or []):
        col = resolve_one(s)
        if col is not None:
            order_by.append(col)

    if not order_by:  # fall back
        for s in default:
            col = resolve_one(s)
            if col is not None:
                order_by.append(col)

    # deterministic tie-break
    if "id" in allowed:
        # if not already sorting by id explicitly, append it (desc to match most feeds)
        ids = {getattr(getattr(ob, "element", None), "name", None) for ob in order_by}
        if "id" not in ids:
            order_by.append(allowed["id"].desc())

    return order_by

def ilike_any(columns: Iterable[Columnish], q: str) -> ColumnElement[bool]:
    pattern = f"%{q}%"
    return or_(*[c.ilike(pattern) for c in columns])
