"""Servicio de avisos — C-15."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.models.aviso import AcknowledgmentAviso, AlcanceAviso, Aviso, SeveridadAviso
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.aviso_repository import (
    AcknowledgmentAvisoRepository,
    AvisoRepository,
)
from app.services.aviso_rules import (
    aplica_a_usuario,
    debe_mostrar_aviso,
    en_vigencia,
)


@dataclass
class AvisoMetricas:
    aviso_id: uuid.UUID
    confirmaciones: int


class AvisoService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._avisos = AvisoRepository(session, tenant_id)
        self._acks = AcknowledgmentAvisoRepository(session, tenant_id)
        self._asignaciones = AsignacionRepository(session, tenant_id)

    async def _contexto_usuario(
        self, user: CurrentUser
    ) -> tuple[set[uuid.UUID], set[uuid.UUID]]:
        asignaciones = await self._asignaciones.list_vigentes_by_usuario(user.id)
        materias = {a.materia_id for a in asignaciones if a.materia_id is not None}
        cohortes = {a.cohorte_id for a in asignaciones if a.cohorte_id is not None}
        return materias, cohortes

    async def _visible_para_usuario(
        self, aviso: Aviso, user: CurrentUser, ahora: datetime
    ) -> bool:
        if not aviso.activo:
            return False
        if not en_vigencia(inicio_en=aviso.inicio_en, fin_en=aviso.fin_en, ahora=ahora):
            return False
        materias, cohortes = await self._contexto_usuario(user)
        alcance = aviso.alcance.value
        if not aplica_a_usuario(
            alcance=alcance,
            materia_id=aviso.materia_id,
            cohorte_id=aviso.cohorte_id,
            rol_destino=aviso.rol_destino,
            user_roles=user.roles,
            user_materia_ids=materias,
            user_cohorte_ids=cohortes,
        ):
            return False
        ack = await self._acks.get_by_aviso_usuario(aviso.id, user.id)
        ya_confirmo = ack is not None
        return debe_mostrar_aviso(requiere_ack=aviso.requiere_ack, ya_confirmo=ya_confirmo)

    async def crear(
        self,
        *,
        alcance: AlcanceAviso,
        materia_id: uuid.UUID | None,
        cohorte_id: uuid.UUID | None,
        rol_destino: str | None,
        severidad: SeveridadAviso,
        titulo: str,
        cuerpo: str,
        inicio_en: datetime,
        fin_en: datetime | None,
        orden: int,
        requiere_ack: bool,
    ) -> Aviso:
        self._validar_alcance(alcance, materia_id, cohorte_id, rol_destino)
        return await self._avisos.add(
            Aviso(
                alcance=alcance,
                materia_id=materia_id,
                cohorte_id=cohorte_id,
                rol_destino=rol_destino,
                severidad=severidad,
                titulo=titulo,
                cuerpo=cuerpo,
                inicio_en=inicio_en,
                fin_en=fin_en,
                orden=orden,
                activo=True,
                requiere_ack=requiere_ack,
            )
        )

    async def actualizar(
        self,
        aviso_id: uuid.UUID,
        *,
        titulo: str | None = None,
        cuerpo: str | None = None,
        inicio_en: datetime | None = None,
        fin_en: datetime | None = None,
        orden: int | None = None,
        activo: bool | None = None,
        requiere_ack: bool | None = None,
        severidad: SeveridadAviso | None = None,
    ) -> Aviso:
        aviso = await self._avisos.get(aviso_id)
        if aviso is None:
            raise ValueError("Aviso no encontrado")
        if titulo is not None:
            aviso.titulo = titulo
        if cuerpo is not None:
            aviso.cuerpo = cuerpo
        if inicio_en is not None:
            aviso.inicio_en = inicio_en
        if fin_en is not None:
            aviso.fin_en = fin_en
        if orden is not None:
            aviso.orden = orden
        if activo is not None:
            aviso.activo = activo
        if requiere_ack is not None:
            aviso.requiere_ack = requiere_ack
        if severidad is not None:
            aviso.severidad = severidad
        await self._session.flush()
        return aviso

    async def eliminar(self, aviso_id: uuid.UUID) -> None:
        aviso = await self._avisos.get(aviso_id)
        if aviso is None:
            raise ValueError("Aviso no encontrado")
        await self._avisos.soft_delete(aviso)

    async def listar_gestion(self) -> list[Aviso]:
        return list(await self._avisos.list_gestion())

    async def listar_para_usuario(self, user: CurrentUser) -> list[Aviso]:
        ahora = datetime.now(timezone.utc)
        visibles: list[Aviso] = []
        for aviso in await self._avisos.list_activos():
            if await self._visible_para_usuario(aviso, user, ahora):
                visibles.append(aviso)
        visibles.sort(key=lambda a: (-a.orden, a.created_at), reverse=False)
        return visibles

    async def confirmar(self, aviso_id: uuid.UUID, user: CurrentUser) -> AcknowledgmentAviso:
        aviso = await self._avisos.get(aviso_id)
        if aviso is None:
            raise ValueError("Aviso no encontrado")
        existente = await self._acks.get_by_aviso_usuario(aviso_id, user.id)
        if existente is not None:
            return existente
        ahora = datetime.now(timezone.utc)
        if not await self._visible_para_usuario(aviso, user, ahora):
            if not en_vigencia(
                inicio_en=aviso.inicio_en, fin_en=aviso.fin_en, ahora=ahora
            ):
                raise ValueError("El aviso no está vigente")
            raise PermissionError("El aviso no aplica a este usuario")
        return await self._acks.add(
            AcknowledgmentAviso(
                aviso_id=aviso_id,
                usuario_id=user.id,
                confirmado_at=ahora,
            )
        )

    async def metricas(self, aviso_id: uuid.UUID) -> AvisoMetricas:
        aviso = await self._avisos.get(aviso_id)
        if aviso is None:
            raise ValueError("Aviso no encontrado")
        return AvisoMetricas(
            aviso_id=aviso_id,
            confirmaciones=await self._acks.count_by_aviso(aviso_id),
        )

    @staticmethod
    def _validar_alcance(
        alcance: AlcanceAviso,
        materia_id: uuid.UUID | None,
        cohorte_id: uuid.UUID | None,
        rol_destino: str | None,
    ) -> None:
        if alcance == AlcanceAviso.por_materia and materia_id is None:
            raise ValueError("Alcance PorMateria requiere materia_id")
        if alcance == AlcanceAviso.por_cohorte and cohorte_id is None:
            raise ValueError("Alcance PorCohorte requiere cohorte_id")
        if alcance == AlcanceAviso.por_rol and rol_destino is None:
            raise ValueError("Alcance PorRol requiere rol_destino")
