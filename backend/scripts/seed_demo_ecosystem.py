"""Datos de demo para video — cohorte, equipo, padrón, calificaciones, finanzas.

Idempotente: se puede ejecutar varias veces vía seed_dev.py.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import AuditAction
from app.core.security import email_blind_index, hash_password
from app.models import AuditLog, Usuario, UsuarioEstado
from app.models.asignacion import Asignacion, RolAsignacion
from app.models.aviso import AlcanceAviso, Aviso, SeveridadAviso
from app.models.calificacion import Calificacion, OrigenCalificacion, UmbralMateria
from app.models.estructura import Carrera, Cohorte, EntidadEstado, Materia
from app.models.liquidacion import SalarioBase, SalarioPlus
from app.models.padron import EntradaPadron, VersionPadron
from app.models.tarea import EstadoTarea, Tarea
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.liquidacion_service import LiquidacionService

DEMO_COHORTE = "2026-1"
DEMO_MATERIA_CODIGO = "MAT01"
DEMO_CARRERA_CODIGO = "TUP"
DEMO_PERIODO_LIQ = "2026-06"
DEMO_VIG_DESDE = date(2026, 3, 1)


def _timestamps() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    return now, now

DEMO_FINANZAS = ("finanzas@demo.local", "Fin1234!", "Carla", "Finanzas", "FINANZAS")

ALUMNOS_DEMO = (
    ("Ana", "García", "ana.garcia@example.com", "A", "Norte"),
    ("Pedro", "López", "pedro.lopez@example.com", "B", "Sur"),
    ("María", "Fernández", "maria.fernandez@example.com", "A", "Norte"),
    ("Juan", "Pérez", "juan.perez@example.com", "B", "Sur"),
)

CALIFICACIONES_DEMO = (
    ("ana.garcia@example.com", "TP1 (Real)", Decimal("78"), None, True),
    ("ana.garcia@example.com", "Reflexion", None, "Satisfactorio", True),
    ("pedro.lopez@example.com", "TP1 (Real)", Decimal("42"), None, False),
    ("pedro.lopez@example.com", "Reflexion", None, "No satisfactorio", False),
    ("maria.fernandez@example.com", "TP1 (Real)", Decimal("55"), None, False),
    ("juan.perez@example.com", "TP1 (Real)", Decimal("88"), None, True),
    ("juan.perez@example.com", "Reflexion", None, "Supera lo esperado", True),
)


async def _get_user(
    session: AsyncSession, tenant_id: uuid.UUID, email: str
) -> Usuario | None:
    repo = UsuarioRepository(session, tenant_id)
    return await repo.get_by_email_hash(email_blind_index(email))


async def _ensure_finanzas(
    session: AsyncSession, tenant_id: uuid.UUID
) -> Usuario:
    email, password, nombre, apellidos, role_code = DEMO_FINANZAS
    repo = UsuarioRepository(session, tenant_id)
    user = await repo.get_by_email_hash(email_blind_index(email))
    if user is None:
        user = await repo.add(
            Usuario(
                email=email,
                email_hash=email_blind_index(email),
                password_hash=hash_password(password),
                nombre=nombre,
                apellidos=apellidos,
                is_active=True,
                estado=UsuarioEstado.activo,
            )
        )
        print(f"Usuario demo creado: {email}")
    rol = await RolRepository(session, tenant_id).get_by_codigo(role_code)
    assert rol is not None
    roles = UsuarioRolRepository(session, tenant_id)
    if role_code not in await roles.list_role_codes_for_user(user.id):
        await roles.assign_role(user.id, rol.id)
        print(f"Rol {role_code} asignado a {email}")
    return user


async def _ensure_cohorte(
    session: AsyncSession, tenant_id: uuid.UUID, carrera_id: uuid.UUID
) -> Cohorte:
    row = await session.execute(
        select(Cohorte).where(
            Cohorte.tenant_id == tenant_id,
            Cohorte.carrera_id == carrera_id,
            Cohorte.nombre == DEMO_COHORTE,
            Cohorte.deleted_at.is_(None),
        )
    )
    cohorte = row.scalar_one_or_none()
    if cohorte is None:
        cohorte = Cohorte(
            tenant_id=tenant_id,
            carrera_id=carrera_id,
            nombre=DEMO_COHORTE,
            anio=2026,
            vig_desde=DEMO_VIG_DESDE,
            estado=EntidadEstado.ACTIVA,
        )
        session.add(cohorte)
        await session.flush()
        print(f"Cohorte demo {DEMO_COHORTE} creada")
    return cohorte


async def _ensure_materia(
    session: AsyncSession, tenant_id: uuid.UUID
) -> Materia:
    row = await session.execute(
        select(Materia).where(
            Materia.tenant_id == tenant_id,
            Materia.codigo == DEMO_MATERIA_CODIGO,
            Materia.deleted_at.is_(None),
        )
    )
    materia = row.scalar_one_or_none()
    if materia is None:
        materia = Materia(
            tenant_id=tenant_id,
            codigo=DEMO_MATERIA_CODIGO,
            nombre="Matemática I",
            plus_grupo="MAT",
            estado=EntidadEstado.ACTIVA,
        )
        session.add(materia)
        await session.flush()
        print("Materia demo MAT01 creada")
    elif materia.plus_grupo != "MAT":
        materia.plus_grupo = "MAT"
        print("Materia MAT01: plus_grupo actualizado")
    return materia


async def _ensure_asignacion(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    usuario_id: uuid.UUID,
    rol: RolAsignacion,
    materia_id: uuid.UUID,
    carrera_id: uuid.UUID,
    cohorte_id: uuid.UUID,
    comisiones: list[str],
) -> Asignacion:
    row = await session.execute(
        select(Asignacion).where(
            Asignacion.tenant_id == tenant_id,
            Asignacion.usuario_id == usuario_id,
            Asignacion.rol == rol,
            Asignacion.materia_id == materia_id,
            Asignacion.cohorte_id == cohorte_id,
            Asignacion.deleted_at.is_(None),
        )
    )
    asig = row.scalar_one_or_none()
    if asig is None:
        asig = Asignacion(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            rol=rol,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            comisiones=comisiones,
            desde=DEMO_VIG_DESDE,
        )
        session.add(asig)
        await session.flush()
        print(f"Asignación {rol.value} creada para usuario {usuario_id}")
    else:
        asig.comisiones = comisiones
    return asig


async def _ensure_padron(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    materia_id: uuid.UUID,
    cohorte_id: uuid.UUID,
    cargado_por: uuid.UUID,
) -> tuple[VersionPadron, list[EntradaPadron]]:
    row = await session.execute(
        select(VersionPadron).where(
            VersionPadron.tenant_id == tenant_id,
            VersionPadron.materia_id == materia_id,
            VersionPadron.cohorte_id == cohorte_id,
            VersionPadron.activa.is_(True),
            VersionPadron.deleted_at.is_(None),
        )
    )
    version = row.scalar_one_or_none()
    if version is not None:
        entradas_row = await session.execute(
            select(EntradaPadron).where(
                EntradaPadron.tenant_id == tenant_id,
                EntradaPadron.version_id == version.id,
                EntradaPadron.deleted_at.is_(None),
            )
        )
        return version, list(entradas_row.scalars().all())

    for old in (
        await session.execute(
            select(VersionPadron).where(
                VersionPadron.tenant_id == tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.cohorte_id == cohorte_id,
                VersionPadron.deleted_at.is_(None),
            )
        )
    ).scalars():
        old.activa = False

    version = VersionPadron(
        tenant_id=tenant_id,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        cargado_por=cargado_por,
        cargado_at=datetime.now(timezone.utc),
        activa=True,
    )
    session.add(version)
    await session.flush()

    entradas: list[EntradaPadron] = []
    for nombre, apellidos, email, comision, regional in ALUMNOS_DEMO:
        entrada = EntradaPadron(
            tenant_id=tenant_id,
            version_id=version.id,
            nombre=nombre,
            apellidos=apellidos,
            email=email,
            comision=comision,
            regional=regional,
        )
        session.add(entrada)
        entradas.append(entrada)
    await session.flush()
    print(f"Padrón demo: {len(entradas)} alumnos")
    return version, entradas


async def _ensure_calificaciones(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    asignacion_id: uuid.UUID,
    materia_id: uuid.UUID,
    entradas: list[EntradaPadron],
) -> None:
    row = await session.execute(
        select(Calificacion.id).where(
            Calificacion.tenant_id == tenant_id,
            Calificacion.asignacion_id == asignacion_id,
            Calificacion.deleted_at.is_(None),
        ).limit(1)
    )
    if row.scalar_one_or_none() is not None:
        return

    by_email: dict[str, EntradaPadron] = {}
    for i, (_, _, email, _, _) in enumerate(ALUMNOS_DEMO):
        if i < len(entradas):
            by_email[email] = entradas[i]
    for email, actividad, nota_num, nota_txt, aprobado in CALIFICACIONES_DEMO:
        entrada = by_email.get(email)
        if entrada is None:
            continue
        session.add(
            Calificacion(
                tenant_id=tenant_id,
                asignacion_id=asignacion_id,
                entrada_padron_id=entrada.id,
                materia_id=materia_id,
                actividad=actividad,
                nota_numerica=nota_num,
                nota_textual=nota_txt,
                aprobado=aprobado,
                origen=OrigenCalificacion.importado,
            )
        )
    await session.flush()
    print("Calificaciones demo cargadas")


async def _ensure_umbral(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    asignacion_id: uuid.UUID,
    materia_id: uuid.UUID,
) -> None:
    row = await session.execute(
        select(UmbralMateria.id).where(
            UmbralMateria.tenant_id == tenant_id,
            UmbralMateria.asignacion_id == asignacion_id,
            UmbralMateria.deleted_at.is_(None),
        )
    )
    if row.scalar_one_or_none() is not None:
        return
    session.add(
        UmbralMateria(
            tenant_id=tenant_id,
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            umbral_pct=60,
            valores_aprobatorios=["Satisfactorio", "Supera lo esperado"],
            agrupaciones_finales=[],
        )
    )
    await session.flush()
    print("Umbral demo configurado (60%)")


async def _ensure_aviso(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    materia_id: uuid.UUID,
    cohorte_id: uuid.UUID,
) -> None:
    row = await session.execute(
        select(Aviso.id).where(
            Aviso.tenant_id == tenant_id,
            Aviso.titulo == "Inicio de parciales — Matemática I",
            Aviso.deleted_at.is_(None),
        )
    )
    if row.scalar_one_or_none() is not None:
        return
    now = datetime.now(timezone.utc)
    aviso = Aviso(
        tenant_id=tenant_id,
        alcance=AlcanceAviso.por_materia,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        severidad=SeveridadAviso.advertencia,
        titulo="Inicio de parciales — Matemática I",
        cuerpo=(
            "Recordatorio: la semana del 23/06 se inician los trabajos prácticos "
            "obligatorios. Revisar cronograma en Moodle."
        ),
        inicio_en=now,
        fin_en=None,
        orden=1,
        activo=True,
        requiere_ack=False,
        created_at=now,
        updated_at=now,
    )
    session.add(aviso)
    await session.flush()
    print("Aviso demo publicado")


async def _ensure_tarea(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    materia_id: uuid.UUID,
    asignado_a: uuid.UUID,
    asignado_por: uuid.UUID,
) -> None:
    row = await session.execute(
        select(Tarea.id).where(
            Tarea.tenant_id == tenant_id,
            Tarea.descripcion.like("Revisar entregas TP1%"),
            Tarea.deleted_at.is_(None),
        )
    )
    if row.scalar_one_or_none() is not None:
        return
    now = datetime.now(timezone.utc)
    session.add(
        Tarea(
            tenant_id=tenant_id,
            materia_id=materia_id,
            asignado_a=asignado_a,
            asignado_por=asignado_por,
            estado=EstadoTarea.pendiente,
            descripcion="Revisar entregas TP1 de comisión B antes del viernes",
            created_at=now,
            updated_at=now,
        )
    )
    await session.flush()
    print("Tarea interna demo creada")


async def _ensure_grilla_salarial(
    session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    row = await session.execute(
        select(SalarioBase.id).where(
            SalarioBase.tenant_id == tenant_id,
            SalarioBase.rol == RolAsignacion.profesor,
            SalarioBase.deleted_at.is_(None),
        ).limit(1)
    )
    if row.scalar_one_or_none() is None:
        created_at, updated_at = _timestamps()
        session.add(
            SalarioBase(
                tenant_id=tenant_id,
                rol=RolAsignacion.profesor,
                monto=Decimal("120000"),
                vig_desde=date(2026, 1, 1),
                created_at=created_at,
                updated_at=updated_at,
            )
        )
        print("Salario base profesor demo")
        await session.flush()
    row_plus = await session.execute(
        select(SalarioPlus.id).where(
            SalarioPlus.tenant_id == tenant_id,
            SalarioPlus.grupo == "MAT",
            SalarioPlus.deleted_at.is_(None),
        ).limit(1)
    )
    if row_plus.scalar_one_or_none() is None:
        created_at, updated_at = _timestamps()
        session.add(
            SalarioPlus(
                tenant_id=tenant_id,
                grupo="MAT",
                rol=RolAsignacion.profesor,
                monto=Decimal("8000"),
                vig_desde=date(2026, 1, 1),
                descripcion="Plus materias básicas",
                created_at=created_at,
                updated_at=updated_at,
            )
        )
        print("Plus salarial MAT demo")
    await session.flush()


async def _ensure_liquidaciones(
    session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    svc = LiquidacionService(session, tenant_id)
    creadas = await svc.calcular_periodo(DEMO_PERIODO_LIQ)
    if creadas:
        print(f"Liquidaciones {DEMO_PERIODO_LIQ}: {len(creadas)} filas")


async def _ensure_audit_samples(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    actor_id: uuid.UUID,
    materia_id: uuid.UUID,
) -> None:
    row = await session.execute(
        select(AuditLog.id).where(AuditLog.tenant_id == tenant_id).limit(1)
    )
    if row.scalar_one_or_none() is not None:
        return
    now = datetime.now(timezone.utc)
    samples = [
        (AuditAction.PADRON_CARGAR, {"filas": 4, "origen": "seed_demo"}),
        (AuditAction.CALIFICACIONES_IMPORTAR, {"actividades": 2, "origen": "seed_demo"}),
        (AuditAction.ASIGNACION_CREAR, {"rol": "PROFESOR", "origen": "seed_demo"}),
    ]
    for accion, detalle in samples:
        session.add(
            AuditLog(
                tenant_id=tenant_id,
                fecha_hora=now,
                actor_id=actor_id,
                materia_id=materia_id,
                accion=accion,
                detalle=detalle,
                filas_afectadas=detalle.get("filas", 1),
                ip="127.0.0.1",
                user_agent="seed_demo_ecosystem",
            )
        )
    await session.flush()
    print("Entradas de auditoría demo")


async def seed_demo_ecosystem(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Carga datos académicos y operativos para el recorrido de demo."""
    carrera_row = await session.execute(
        select(Carrera).where(
            Carrera.tenant_id == tenant_id,
            Carrera.codigo == DEMO_CARRERA_CODIGO,
            Carrera.deleted_at.is_(None),
        )
    )
    carrera = carrera_row.scalar_one_or_none()
    if carrera is None:
        print("Sin carrera TUP — omitiendo ecosistema demo")
        return

    cohorte = await _ensure_cohorte(session, tenant_id, carrera.id)
    materia = await _ensure_materia(session, tenant_id)
    await _ensure_finanzas(session, tenant_id)

    prof_a = await _get_user(session, tenant_id, "prof-a@demo.local")
    prof_b = await _get_user(session, tenant_id, "prof-b@demo.local")
    coord = await _get_user(session, tenant_id, "coord@demo.local")
    admin = await _get_user(session, tenant_id, "admin@demo.local")
    if prof_a is None or prof_b is None or coord is None or admin is None:
        print("Faltan usuarios demo — omitiendo asignaciones")
        return

    asig_prof_a = await _ensure_asignacion(
        session,
        tenant_id,
        usuario_id=prof_a.id,
        rol=RolAsignacion.profesor,
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        comisiones=["A"],
    )
    await _ensure_asignacion(
        session,
        tenant_id,
        usuario_id=prof_b.id,
        rol=RolAsignacion.profesor,
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        comisiones=["B"],
    )
    await _ensure_asignacion(
        session,
        tenant_id,
        usuario_id=coord.id,
        rol=RolAsignacion.coordinador,
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        comisiones=[],
    )

    _version, entradas = await _ensure_padron(
        session,
        tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        cargado_por=prof_a.id,
    )
    await _ensure_calificaciones(
        session,
        tenant_id,
        asignacion_id=asig_prof_a.id,
        materia_id=materia.id,
        entradas=entradas,
    )
    await _ensure_umbral(
        session, tenant_id, asignacion_id=asig_prof_a.id, materia_id=materia.id
    )
    await _ensure_aviso(
        session, tenant_id, materia_id=materia.id, cohorte_id=cohorte.id
    )
    await _ensure_tarea(
        session,
        tenant_id,
        materia_id=materia.id,
        asignado_a=prof_a.id,
        asignado_por=coord.id,
    )
    await _ensure_grilla_salarial(session, tenant_id)
    await _ensure_liquidaciones(session, tenant_id)
    await _ensure_audit_samples(
        session, tenant_id, actor_id=admin.id, materia_id=materia.id
    )
