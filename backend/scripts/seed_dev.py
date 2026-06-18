"""Seed idempotente para desarrollo local / Docker.

Crea tenant `demo`, RBAC y usuario ADMIN para login en la SPA.

Uso:
    python scripts/seed_dev.py

Credenciales:
    tenant: demo
    email:  admin@demo.local
    pass:   Admin1234!
"""

import asyncio
import uuid

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import dispose_db, get_session_factory, init_db
from app.core.security import email_blind_index, hash_password
from app.models import Tenant, Usuario, UsuarioEstado
from app.models.estructura import Carrera, EntidadEstado, Materia
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.rbac_seed import seed_tenant_rbac
from scripts.seed_demo_ecosystem import seed_demo_ecosystem

DEMO_TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEMO_SLUG = "demo"
DEMO_EMAIL = "admin@demo.local"
DEMO_PASSWORD = "Admin1234!"

DEMO_USERS = (
    ("prof-a@demo.local", "Prof1234!", "Ana", "Profesora A", "PROFESOR"),
    ("prof-b@demo.local", "Prof1234!", "Luis", "Profesor B", "PROFESOR"),
    ("coord@demo.local", "Coord1234!", "Luis", "Coordinador", "COORDINADOR"),
)


async def seed_dev() -> None:
    settings = get_settings()
    init_db(settings.database_url)
    factory = get_session_factory()

    async with factory() as session:
        existing = await session.execute(
            select(Tenant.id).where(Tenant.slug == DEMO_SLUG, Tenant.deleted_at.is_(None))
        )
        tenant_id = existing.scalar_one_or_none()
        if tenant_id is None:
            session.add(
                Tenant(id=DEMO_TENANT_ID, nombre="Instituto Demo", slug=DEMO_SLUG)
            )
            await session.flush()
            tenant_id = DEMO_TENANT_ID
            print(f"Tenant creado: {DEMO_SLUG}")
        else:
            print(f"Tenant existente: {DEMO_SLUG}")

        await seed_tenant_rbac(session, tenant_id)

        user_repo = UsuarioRepository(session, tenant_id)
        user = await user_repo.get_by_email_hash(email_blind_index(DEMO_EMAIL))
        if user is None:
            user = await user_repo.add(
                Usuario(
                    email=DEMO_EMAIL,
                    email_hash=email_blind_index(DEMO_EMAIL),
                    password_hash=hash_password(DEMO_PASSWORD),
                    is_active=True,
                    estado=UsuarioEstado.activo,
                )
            )
            print(f"Usuario creado: {DEMO_EMAIL}")
        else:
            user.password_hash = hash_password(DEMO_PASSWORD)
            print(f"Usuario existente (password sincronizado): {DEMO_EMAIL}")

        rol = await RolRepository(session, tenant_id).get_by_codigo("ADMIN")
        assert rol is not None
        usuario_roles = UsuarioRolRepository(session, tenant_id)
        if "ADMIN" not in await usuario_roles.list_role_codes_for_user(user.id):
            await usuario_roles.assign_role(user.id, rol.id)
            print("Rol ADMIN asignado")
        else:
            print("Rol ADMIN ya asignado")

        rol_repo = RolRepository(session, tenant_id)
        for email, password, nombre, apellidos, role_code in DEMO_USERS:
            demo_user = await user_repo.get_by_email_hash(email_blind_index(email))
            if demo_user is None:
                demo_user = await user_repo.add(
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
            rol = await rol_repo.get_by_codigo(role_code)
            if rol and role_code not in await usuario_roles.list_role_codes_for_user(demo_user.id):
                await usuario_roles.assign_role(demo_user.id, rol.id)
                print(f"Rol {role_code} asignado a {email}")

        carrera_exists = await session.execute(
            select(Carrera.id).where(
                Carrera.tenant_id == tenant_id,
                Carrera.codigo == "TUP",
                Carrera.deleted_at.is_(None),
            )
        )
        if carrera_exists.scalar_one_or_none() is None:
            session.add(
                Carrera(
                    tenant_id=tenant_id,
                    codigo="TUP",
                    nombre="Tecnicatura Universitaria",
                    estado=EntidadEstado.ACTIVA,
                )
            )
            print("Carrera demo TUP creada")

        materia_exists = await session.execute(
            select(Materia.id).where(
                Materia.tenant_id == tenant_id,
                Materia.codigo == "MAT01",
                Materia.deleted_at.is_(None),
            )
        )
        if materia_exists.scalar_one_or_none() is None:
            session.add(
                Materia(
                    tenant_id=tenant_id,
                    codigo="MAT01",
                    nombre="Matemática I",
                    plus_grupo="MAT",
                    estado=EntidadEstado.ACTIVA,
                )
            )
            print("Materia demo MAT01 creada")

        await seed_demo_ecosystem(session, tenant_id)

        await session.commit()

    await dispose_db()
    print("\n--- Login dev ---")
    print(f"  tenant:   {DEMO_SLUG}")
    print(f"  admin:    {DEMO_EMAIL} / {DEMO_PASSWORD}")
    print(f"  prof-a:   prof-a@demo.local / Prof1234!  (comisión A)")
    print(f"  prof-b:   prof-b@demo.local / Prof1234!  (comisión B)")
    print(f"  coord:    coord@demo.local / Coord1234!")
    print(f"  finanzas: finanzas@demo.local / Fin1234!")
    print(f"  API:      http://localhost:8000")
    print(f"  SPA:      http://localhost:5173")


if __name__ == "__main__":
    asyncio.run(seed_dev())
