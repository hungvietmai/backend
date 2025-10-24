from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.error_handlers import register_exception_handlers
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- startup ----
    setup_logging('INFO')
    yield
    # ---- shutdown ----

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG or settings.is_dev,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list if settings.CORS_ORIGINS else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=f"/{settings.API_PREFIX}/{settings.API_VERSION}")

    # Basic health endpoint
    @app.get("/healthz", tags=["_ops"])
    def healthz():
        return {"status": "ok"}

    return app


# ASGI entrypoint: `uvicorn app.main:app`
app = create_app()
