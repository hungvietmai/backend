from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class ReviewCreate(BaseModel):
    user_id: int
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = None
    body: Optional[str] = None

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    title: Optional[str] = None
    body: Optional[str] = None

class ReviewOut(BaseModel):
    id: int
    product_id: int
    user_id: int | None
    rating: int
    title: Optional[str]
    body: Optional[str]
    is_published: bool
    created_at: str
    model_config = ConfigDict(from_attributes=True)

class ReviewModerateIn(BaseModel):
    is_published: bool
