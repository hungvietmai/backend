from __future__ import annotations
from typing import Any, Mapping, Optional
from pydantic import BaseModel, ConfigDict

class Problem(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: Optional[str] = None
    instance: Optional[str] = None
    errors: Optional[Mapping[str, Any]] = None  # field-level issues

    model_config = ConfigDict(extra="ignore")
