# app/services/cart_service.py
from __future__ import annotations
from sqlalchemy.orm import Session
from app.repositories.cart_repo import CartRepository
from app.repositories.inventory_repo import InventoryRepository
from app.models.catalog import ProductVariant, Product
from app.exceptions import NotFound, BadRequest


class CartService:
    def __init__(self, db: Session):
        self.db = db
        self.carts = CartRepository(db)
        self.inv = InventoryRepository(db)

    def _unit_price_for(self, variant: ProductVariant) -> int:
        product: Product = variant.product
        return variant.price_cents if variant.price_cents is not None else product.base_price_cents

    def get_cart(self, user_id: int):
        cart = self.carts.get_open_for_user(user_id) or self.carts.create_for_user(user_id)
        # server-side subtotal (don’t persist; just attach for response mapping)
        cart.subtotal_cents = sum(it.line_total_cents for it in cart.items)  # type: ignore[attr-defined]
        return cart

    def add_item(self, user_id: int, variant_id: int, qty: int):
        if qty <= 0:
            raise BadRequest(detail="Quantity must be > 0")

        cart = self.carts.get_open_for_user(user_id) or self.carts.create_for_user(user_id)
        variant = self.inv.load_variant(variant_id)
        if not variant or not variant.product or not variant.product.is_active:
            raise NotFound(detail="Variant not available")

        if qty > (variant.stock_qty or 0):
            raise BadRequest(detail="Insufficient stock")

        price = self._unit_price_for(variant)
        item = self.carts.add_item(
            cart,
            variant_id=variant_id,
            qty=qty,
            unit_price_cents=price,
        )
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_item(self, user_id: int, item_id: int, qty: int):
        if qty <= 0:
            raise BadRequest(detail="Quantity must be > 0")

        cart = self.carts.get_open_for_user(user_id) or self.carts.create_for_user(user_id)
        item = self.carts.get_item(item_id)
        if not item or item.cart_id != cart.id:
            raise NotFound(detail="Cart item not found")

        variant = self.inv.load_variant(item.variant_id)
        if not variant:
            raise NotFound(detail="Variant not found")

        if qty > (variant.stock_qty or 0):
            raise BadRequest(detail="Insufficient stock")

        item = self.carts.update_item_qty(item, qty)
        self.db.commit()
        self.db.refresh(item)
        return item

    def remove_item(self, user_id: int, item_id: int) -> None:
        cart = self.carts.get_open_for_user(user_id) or self.carts.create_for_user(user_id)
        item = self.carts.get_item(item_id)
        if not item or item.cart_id != cart.id:
            return
        self.carts.remove_item(item)
        self.db.commit()
