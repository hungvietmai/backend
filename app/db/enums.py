from __future__ import annotations

from enum import Enum as PyEnum


# ---------- Auth / Users ----------
class UserRoleEnum(str, PyEnum):
    admin = "admin"
    customer = "customer"


# ---------- Cart ----------
class CartStatusEnum(str, PyEnum):
    open = "open"
    checked_out = "checked_out"
    abandoned = "abandoned"


# ---------- Orders ----------
class OrderStatusEnum(str, PyEnum):
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"
    fulfilled = "fulfilled"
    refunded = "refunded"


# ---------- Payments ----------
class PaymentStatusEnum(str, PyEnum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"
    voided = "voided"


class PaymentMethodEnum(str, PyEnum):
    cod = "cod"
    card = "card"
    momo = "momo"
    zalopay = "zalopay"


# ---------- Shipments ----------
class ShipmentStatusEnum(str, PyEnum):
    pending = "pending"
    packed = "packed"
    in_transit = "in_transit"
    delivered = "delivered"
    cancelled = "cancelled"


# ---------- Inventory ----------
class InventoryMovementType(str, PyEnum):
    stock_in = "stock_in"            # manual add / purchase
    reserve = "reserve"              # reserve on add-to-cart
    unreserve = "unreserve"          # cart removal / expiration
    sold = "sold"                    # order placed/paid
    return_in = "return_in"          # returned items
    cancel_adjust = "cancel_adjust"  # order cancelled, add back
    manual_adjust = "manual_adjust"  # corrections


# ---------- Returns ----------
class ReturnStatusEnum(str, PyEnum):
    requested = "requested"
    approved = "approved"
    rejected = "rejected"
    received = "received"
    refunded = "refunded"
    closed = "closed"


__all__ = [
    "UserRoleEnum",
    "CartStatusEnum",
    "OrderStatusEnum",
    "PaymentStatusEnum",
    "PaymentMethodEnum",
    "ShipmentStatusEnum",
    "InventoryMovementType",
    "ReturnStatusEnum",
]
