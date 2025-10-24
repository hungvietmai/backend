from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# I/O models
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=255)
    model_config = ConfigDict(extra="forbid")

class LoginIn(BaseModel):
    email: EmailStr
    password: str
    model_config = ConfigDict(extra="forbid")

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MeOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ChangePasswordIn(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)
    model_config = ConfigDict(extra="forbid")

class ForgotPasswordIn(BaseModel):
    email: EmailStr
    model_config = ConfigDict(extra="forbid")

class ForgotPasswordOut(BaseModel):
    reset_token: str
    expires_minutes: int

class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=10)
    new_password: str = Field(min_length=8, max_length=128)
    model_config = ConfigDict(extra="forbid")