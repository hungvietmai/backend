from fastapi import APIRouter

from .admin import products as admin_products
from .admin import orders as admin_orders
from .admin import reviews as admin_reviews
from .admin import users as admin_users
from .admin import catalog as admin_catalog
from .admin import returns as admin_returns
from .admin import inventory as admin_inventory
from . import auth, cart, orders, products, reviews, catalog, addresses, returns

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(reviews.router)
api_router.include_router(catalog.router)
api_router.include_router(addresses.router)
api_router.include_router(returns.router)

# admin
api_router.include_router(admin_products.router)
api_router.include_router(admin_reviews.router)
api_router.include_router(admin_orders.router)
api_router.include_router(admin_users.router)
api_router.include_router(admin_catalog.router)
api_router.include_router(admin_returns.router)
api_router.include_router(admin_inventory.router)