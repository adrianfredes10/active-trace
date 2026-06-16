"""Servicio de padrón — C-09."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.moodle_ws import MoodleUnavailable, MoodleWSClient
from app.models.padron import EntradaPadron, VersionPadron
from app.repositories.padron_repository import (
    EntradaPadronRepository,
    VersionPadronRepository,
)
from app.services.padron_parser import FilaPadron, PadronParseError, parse_padron_file

logger = logging.getLogger(__name__)


class PadronService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._versiones = VersionPadronRepository(session, tenant_id)
        self._entradas = EntradaPadronRepository(session, tenant_id)

    def preview_archivo(self, content: bytes, filename: str) -> list[FilaPadron]:
        return parse_padron_file(content, filename)

    async def importar_padron(
        self,
        *,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        cargado_por: uuid.UUID,
        filas: list[FilaPadron],
    ) -> VersionPadron:
        if not filas:
            raise ValueError("El padrón no puede estar vacío")

        await self._versiones.desactivar_contexto(materia_id, cohorte_id)

        version = VersionPadron(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            cargado_por=cargado_por,
            cargado_at=datetime.now(timezone.utc),
            activa=True,
        )
        await self._versiones.add(version)

        entradas = [
            EntradaPadron(
                version_id=version.id,
                nombre=f.nombre,
                apellidos=f.apellidos,
                email=f.email,
                comision=f.comision,
                regional=f.regional,
                usuario_id=None,
            )
            for f in filas
        ]
        await self._entradas.add_many(entradas)
        logger.info(
            "padron importado version=%s filas=%s", version.id, len(entradas)
        )
        return version

    async def importar_desde_moodle(
        self,
        *,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        cargado_por: uuid.UUID,
        client: MoodleWSClient,
        course_id: int,
    ) -> VersionPadron:
        try:
            participants = await client.fetch_participants(course_id)
        except MoodleUnavailable:
            raise
        filas = [
            FilaPadron(
                nombre=p.nombre,
                apellidos=p.apellidos,
                email=p.email,
            )
            for p in participants
        ]
        return await self.importar_padron(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            cargado_por=cargado_por,
            filas=filas,
        )

    async def get_version_activa(
        self, materia_id: uuid.UUID, cohorte_id: uuid.UUID
    ) -> VersionPadron | None:
        return await self._versiones.get_activa(materia_id, cohorte_id)

    async def list_entradas_activas(
        self, materia_id: uuid.UUID, cohorte_id: uuid.UUID
    ) -> list[EntradaPadron]:
        version = await self._versiones.get_activa(materia_id, cohorte_id)
        if version is None:
            return []
        return list(await self._entradas.list_by_version(version.id))

    async def vaciar_datos_materia(
        self, materia_id: uuid.UUID, cargado_por: uuid.UUID
    ) -> int:
        """RN-04: solo versiones cargadas por el actor en esa materia."""
        versiones = await self._versiones.list_by_cargador_materia(
            cargado_por, materia_id
        )
        count = 0
        for version in versiones:
            if version.activa:
                version.activa = False
            await self._versiones.soft_delete(version)
            entradas = await self._entradas.list_by_version(version.id)
            for entrada in entradas:
                await self._entradas.soft_delete(entrada)
            count += 1
        await self._session.flush()
        logger.info(
            "padron vaciado materia=%s por=%s versiones=%s",
            materia_id,
            cargado_por,
            count,
        )
        return count
