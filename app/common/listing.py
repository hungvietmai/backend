from __future__ import annotations
from typing import Any, Iterable, Mapping, Sequence, TypeVar, cast
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql import ColumnElement, Select

T = TypeVar("T")
Col = ColumnElement[Any] | InstrumentedAttribute[Any]  # “column-ish”

def paginate(db: Session, stmt: Select[tuple[T]], limit: int, offset: int) -> tuple[list[T], int]:
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = cast(list[T], db.execute(stmt.limit(limit).offset(offset)).scalars().all())
    return items, total

def safe_order_by(sort: Sequence[str], allowed: Mapping[str, Col], default: Sequence[str]) -> list[ColumnElement[Any]]:
    def resolve(s: str) -> ColumnElement[Any] | None:
        desc = s.startswith("-"); field = s[1:] if desc else s
        col = allowed.get(field)
        if col is None: return None
        return cast(ColumnElement[Any], col.desc() if desc else col.asc())
    out: list[ColumnElement[Any]] = [e for s in (sort or []) if (e := resolve(s)) is not None]
    if not out:
        out = [e for s in default if (e := resolve(s)) is not None]
    if "id" in allowed:  # deterministic tie-break
        names = {getattr(getattr(e, "element", None), "name", None) for e in out}
        if "id" not in names:
            out.append(cast(ColumnElement[Any], allowed["id"]).desc())
    return out

def ilike_any(cols: Iterable[Col], q: str):
    return or_(*[cast(ColumnElement[Any], c).ilike(f"%{q}%") for c in cols])
