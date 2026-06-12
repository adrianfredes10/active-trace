import uuid

import pytest

from app.core.database import get_session_factory
from app.core.security import (
    TOKEN_TYPE_ACCESS,
    decode_token,
    email_blind_index,
    hash_password,
)
from app.models import Tenant, Usuario
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.auth_service import AuthService
from app.services.rbac_seed import seed_tenant_rbac

pytestmark = pytest.mark.asyncio

TENANT = uuid.UUID("00000000-0000-0000-0000-0000000000a4")
EMAIL = "roles@activia.test"
PW = "S3cret!pass"


async def _setup_with_role(codigo_rol: str | None) -> None:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT, nombre="H", slug="h-rbac"))
        await session.flush()
        await seed_tenant_rbac(session, TENANT)
        user = await UsuarioRepository(session, TENANT).add(
            Usuario(
                email=EMAIL,
                email_hash=email_blind_index(EMAIL),
                password_hash=hash_password(PW),
            )
        )
        if codigo_rol:
            rol = await RolRepository(session, TENANT).get_by_codigo(codigo_rol)
            assert rol is not None
            await UsuarioRolRepository(session, TENANT).assign_role(user.id, rol.id)
        await session.commit()


async def test_login_token_has_roles(session, settings) -> None:
    await _setup_with_role("PROFESOR")
    factory = get_session_factory()
    async with factory() as session:
        result = await AuthService(session, TENANT).login(EMAIL, PW)
        assert result.tokens is not None
        claims = decode_token(result.tokens.access_token, expected_type=TOKEN_TYPE_ACCESS)
        assert claims["roles"] == ["PROFESOR"]


async def test_login_token_empty_roles_without_assignment(session, settings) -> None:
    await _setup_with_role(None)
    factory = get_session_factory()
    async with factory() as session:
        result = await AuthService(session, TENANT).login(EMAIL, PW)
        assert result.tokens is not None
        claims = decode_token(result.tokens.access_token, expected_type=TOKEN_TYPE_ACCESS)
        assert claims["roles"] == []
