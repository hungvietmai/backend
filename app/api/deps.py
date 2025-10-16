from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token
from app.db.enums import UserRoleEnum
from app.db.session import SessionLocal
from app.models.auth import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/{settings.API_VERSION}/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Strongly-typed claims so Pylance/MyPy are happy
class TokenClaims(BaseModel):
    sub: str
    exp: int
    iat: int
    role: Optional[str] = None

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_token(token)                 # dict[str, Any]
        claims = TokenClaims.model_validate(payload)  # validates & narrows types
        try:
            user_id = int(claims.sub)                # safe now; sub is a str
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    except (JWTError, ValidationError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # SQLAlchemy 2.0: use Session.get instead of Query.get
    user = db.get(User, user_id)
    if not user or not user.is_active or user.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")
    return user

def require_admin(current: User = Depends(get_current_user)) -> User:
    if current.role != UserRoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    return current