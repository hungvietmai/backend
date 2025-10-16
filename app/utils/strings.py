import re
from typing import Callable, Optional

_slug_re = re.compile(r"[^a-z0-9]+")
def slugify(text: str) -> str:
    s = text.lower().strip()
    s = _slug_re.sub("-", s).strip("-")
    return s or "item"

def slugify_unique(check: Callable[[str], Optional[object]], name: str) -> str:
    """Generate a slug and ensure uniqueness using the `check(slug)` function (returns model or None)."""
    base = slugify(name)
    slug = base
    i = 2
    while check(slug) is not None:
        slug = f"{base}-{i}"
        i += 1
    return slug
