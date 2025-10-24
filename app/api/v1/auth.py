from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.auth import (
    RegisterIn, LoginIn, TokenOut, MeOut,
    ForgotPasswordIn, ForgotPasswordOut, ResetPasswordIn, ChangePasswordIn,
)
from app.schemas.common import Problem
from app.services.auth_service import AuthService
from app.models.auth import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=MeOut, status_code=status.HTTP_201_CREATED,
             responses={400: {"model": Problem}, 409: {"model": Problem}, 422: {"model": Problem}})
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    return AuthService(db).register(payload.email, payload.password, payload.full_name)

@router.post("/login", response_model=TokenOut, responses={401: {"model": Problem}, 422: {"model": Problem}})
def login(payload: LoginIn, db: Session = Depends(get_db)):
    token = AuthService(db).login(payload.email, payload.password)
    return TokenOut(access_token=token)

@router.get("/me", response_model=MeOut, responses={401: {"model": Problem}})
def me(current: User = Depends(get_current_user)):
    return current

@router.post("/forgot-password", response_model=ForgotPasswordOut, status_code=status.HTTP_200_OK)
def forgot_password(payload: ForgotPasswordIn, db: Session = Depends(get_db)):
    token, minutes = AuthService(db).forgot_password(payload.email)
    return ForgotPasswordOut(reset_token=token, expires_minutes=minutes)

@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT,
             responses={401: {"model": Problem}, 400: {"model": Problem}, 422: {"model": Problem}})
def reset_password(payload: ResetPasswordIn, db: Session = Depends(get_db)):
    AuthService(db).reset_password(payload.token, payload.new_password)

@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT,
             responses={401: {"model": Problem}, 400: {"model": Problem}, 422: {"model": Problem}})
def change_password(payload: ChangePasswordIn, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    AuthService(db).change_password(current.id, payload.new_password)
