from __future__ import annotations
from datetime import datetime, timezone
import random

def gen_order_number(dt: datetime | None = None) -> str:
    dt = dt or datetime.now(timezone.utc)
    return f"FS-{dt.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
