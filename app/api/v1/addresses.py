from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.address import AddressCreate, AddressUpdate, AddressOut
from app.services.address_service import AddressService
from app.models.auth import User

router = APIRouter(prefix="/addresses", tags=["addresses"])

@router.get("", response_model=List[AddressOut])
def list_my_addresses(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [AddressOut.model_validate(a, from_attributes=True) for a in AddressService(db).list_my(current.id)]

@router.post("", response_model=AddressOut, status_code=status.HTTP_201_CREATED)
def create_address(payload: AddressCreate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = AddressService(db).create(current.id, payload.model_dump())
    return AddressOut.model_validate(row, from_attributes=True)

@router.patch("/{address_id}", response_model=AddressOut)
def update_address(address_id: int, payload: AddressUpdate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = AddressService(db).update(current.id, address_id, payload.model_dump(exclude_none=True))
    return AddressOut.model_validate(row, from_attributes=True)

@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    AddressService(db).delete(current.id, address_id)
    return

@router.post("/{address_id}/make-default", response_model=AddressOut)
def make_default(address_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = AddressService(db).make_default(current.id, address_id)
    return AddressOut.model_validate(row, from_attributes=True)
