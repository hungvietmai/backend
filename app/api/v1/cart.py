from __future__ import annotations
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.cart import CartItemIn, CartItemUpdate, CartItemOut, CartOut
from app.services.cart_service import CartService
from app.models.auth import User

router = APIRouter(prefix="/cart", tags=["cart"])

@router.get("", response_model=CartOut)
def get_cart(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = CartService(db).get_cart(current.id)
    return CartOut(
        id=cart.id, user_id=cart.user_id,
        items=[CartItemOut.model_validate(i) for i in cart.items],
        subtotal_cents=sum(i.line_total_cents for i in cart.items),
    )

@router.post("/items", response_model=CartItemOut, status_code=status.HTTP_201_CREATED)
def add_item(payload: CartItemIn, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    it = CartService(db).add_item(current.id, payload.variant_id, payload.qty)
    return it

@router.patch("/items/{item_id}", response_model=CartItemOut)
def update_item(item_id: int, payload: CartItemUpdate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    it = CartService(db).update_item(current.id, item_id, payload.qty)
    return it

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item(item_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    CartService(db).remove_item(current.id, item_id)
    return
