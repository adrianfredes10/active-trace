from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers.audit import router as audit_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.estructura import router as estructura_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.rbac import router as rbac_router
from app.core.config import get_settings
from app.core.database import dispose_db, init_db
from app.core.logging import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.core.observability import setup_observability


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db(settings.database_url)
    yield
    await dispose_db()


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging()

    app = FastAPI(title="activia-trace", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    setup_observability(
        app,
        enabled=settings.otel_enabled,
        service_name=settings.otel_service_name,
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(rbac_router)
    app.include_router(audit_router)
    app.include_router(estructura_router)
    return app


app = create_app()
