import uuid

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.dependencies import CurrentUser, get_current_user
from app.core.security import create_access_token
from app.core.tenancy import get_tenant

pytestmark = pytest.mark.asyncio


def _creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


async def test_get_current_user_without_header(settings) -> None:
    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials=None)
    assert exc.value.status_code == 401


async def test_get_current_user_valid_token(settings) -> None:
    uid, tid = str(uuid.uuid4()), str(uuid.uuid4())
    token = create_access_token(user_id=uid, tenant_id=tid, roles=["ADMIN"])
    user = await get_current_user(credentials=_creds(token))
    assert str(user.id) == uid
    assert str(user.tenant_id) == tid
    assert user.roles == ["ADMIN"]


async def test_get_current_user_invalid_token(settings) -> None:
    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials=_creds("basura"))
    assert exc.value.status_code == 401


async def test_get_tenant_returns_session_tenant(settings) -> None:
    tid = uuid.uuid4()
    user = CurrentUser(id=uuid.uuid4(), tenant_id=tid, roles=[])
    assert await get_tenant(user=user) == tid
