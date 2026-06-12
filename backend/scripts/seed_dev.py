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
from app.models import Tenant, Usuario
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.rbac_seed import seed_tenant_rbac

DEMO_TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEMO_SLUG = "demo"
DEMO_EMAIL = "admin@demo.local"
DEMO_PASSWORD = "Admin1234!"


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
                )
            )
            print(f"Usuario creado: {DEMO_EMAIL}")
        else:
            print(f"Usuario existente: {DEMO_EMAIL}")

        rol = await RolRepository(session, tenant_id).get_by_codigo("ADMIN")
        assert rol is not None
        await UsuarioRolRepository(session, tenant_id).assign_role(user.id, rol.id)
        await session.commit()

    await dispose_db()
    print("\n--- Login dev ---")
    print(f"  tenant:   {DEMO_SLUG}")
    print(f"  email:    {DEMO_EMAIL}")
    print(f"  password: {DEMO_PASSWORD}")
    print(f"  API:      http://localhost:8000")
    print(f"  SPA:      http://localhost:5173")


if __name__ == "__main__":
    asyncio.run(seed_dev())
