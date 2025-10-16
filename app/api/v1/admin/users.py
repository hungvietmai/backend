from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.schemas.page import Page
from app.schemas.user import UserOut
from app.services.admin.user_service import AdminUserService
from app.db.enums import UserRoleEnum

router = APIRouter(prefix="/admin/users", tags=["admin:users"], dependencies=[Depends(require_admin)])

@router.get("", response_model=Page[UserOut])
def list_users(q: str | None = None, role: str | None = None, is_active: bool | None = None,
               sort: list[str] = Query(["-created_at"]), limit: int = Query(50, ge=1, le=200),
               offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return AdminUserService(db).list_page(q=q, role=role, is_active=is_active, sort=sort, limit=limit, offset=offset)

@router.post("/{user_id}/role")
def set_role(user_id: int, role: UserRoleEnum, db: Session = Depends(get_db)):
    return AdminUserService(db).set_role(user_id, role)

@router.post("/{user_id}/activate")
def activate(user_id: int, db: Session = Depends(get_db)):
    return AdminUserService(db).set_active(user_id, True)

@router.post("/{user_id}/deactivate")
def deactivate(user_id: int, db: Session = Depends(get_db)):
    return AdminUserService(db).set_active(user_id, False)

@router.delete("/{user_id}")
def soft_delete(user_id: int, db: Session = Depends(get_db)):
    return AdminUserService(db).soft_delete(user_id)

@router.post("/{user_id}/restore")
def restore(user_id: int, db: Session = Depends(get_db)):
    return AdminUserService(db).restore(user_id)
