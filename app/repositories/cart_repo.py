from __future__ import annotations
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cart import Cart, CartItem
from app.db.enums import CartStatusEnum

class CartRepository:
    def __init__(self, db: Session): self.db = db

    # --- cart reads ---
    def get(self, cart_id: int) -> Optional[Cart]:
        return self.db.get(Cart, cart_id)

    def get_open_for_user(self, user_id: int) -> Optional[Cart]:
        stmt = select(Cart).where(
            Cart.user_id == user_id,
            Cart.status == CartStatusEnum.open,
            Cart.deleted_at.is_(None),
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_items(self, cart_id: int) -> Sequence[CartItem]:
        stmt = select(CartItem).where(CartItem.cart_id == cart_id).order_by(CartItem.created_at.asc())
        return self.db.execute(stmt).scalars().all()

    # --- cart writes (no commits) ---
    def create_for_user(self, user_id: int) -> Cart:
        row = Cart(user_id=user_id, status=CartStatusEnum.open)
        self.db.add(row); return row

    def set_checked_out(self, cart: Cart) -> None:
        cart.status = CartStatusEnum.checked_out
        self.db.add(cart)

    # --- items ---
    def get_item(self, item_id: int) -> Optional[CartItem]:
        return self.db.get(CartItem, item_id)

    def add_item(self, cart: Cart, *, variant_id: int, qty: int, unit_price_cents: int) -> CartItem:
        # merge if same variant exists (unique (cart_id, variant_id))
        for it in cart.items:
            if it.variant_id == variant_id:
                it.qty += qty
                it.unit_price_cents = unit_price_cents
                it.line_total_cents = it.qty * it.unit_price_cents
                self.db.add(it)
                return it
        row = CartItem(
            cart_id=cart.id,
            variant_id=variant_id,
            qty=qty,
            unit_price_cents=unit_price_cents,
            line_total_cents=qty * unit_price_cents,
        )
        self.db.add(row); return row

    def update_item_qty(self, item: CartItem, qty: int) -> CartItem:
        item.qty = qty
        item.line_total_cents = qty * item.unit_price_cents
        self.db.add(item); return item

    def remove_item(self, item: CartItem) -> None:
        self.db.delete(item)
