from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers.facturas import router as facturas_router
from app.api.v1.routers.liquidaciones import router as liquidaciones_router
from app.api.v1.routers.analisis import router as analisis_router
from app.api.v1.routers.fechas_academicas import router as fechas_academicas_router
from app.api.v1.routers.inbox import router as inbox_router
from app.api.v1.routers.perfil import router as perfil_router
from app.api.v1.routers.programas import router as programas_router
from app.api.v1.routers.tareas import router as tareas_router
from app.api.v1.routers.avisos import router as avisos_router
from app.api.v1.routers.coloquios import router as coloquios_router
from app.api.v1.routers.encuentros import router as encuentros_router
from app.api.v1.routers.guardias import router as guardias_router
from app.api.v1.routers.comunicaciones import router as comunicaciones_router
from app.api.v1.routers.calificaciones import router as calificaciones_router
from app.api.v1.routers.padron import router as padron_router
from app.api.v1.routers.equipos import router as equipos_router
from app.api.v1.routers.asignaciones import router as asignaciones_router
from app.api.v1.routers.auditoria import router as auditoria_router
from app.api.v1.routers.audit import router as audit_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.estructura import router as estructura_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.rbac import router as rbac_router
from app.api.v1.routers.usuarios import router as usuarios_router
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
    app.include_router(auditoria_router)
    app.include_router(estructura_router)
    app.include_router(usuarios_router)
    app.include_router(asignaciones_router)
    app.include_router(equipos_router)
    app.include_router(padron_router)
    app.include_router(calificaciones_router)
    app.include_router(analisis_router)
    app.include_router(comunicaciones_router)
    app.include_router(encuentros_router)
    app.include_router(guardias_router)
    app.include_router(coloquios_router)
    app.include_router(avisos_router)
    app.include_router(tareas_router)
    app.include_router(programas_router)
    app.include_router(fechas_academicas_router)
    app.include_router(perfil_router)
    app.include_router(inbox_router)
    app.include_router(liquidaciones_router)
    app.include_router(facturas_router)
    return app


app = create_app()
