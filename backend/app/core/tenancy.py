"""Resolución del tenant desde la sesión autenticada (C-03).

El scope de tenant a nivel de datos (row-level) vive en
`app/repositories/base.py` (C-02). Aquí se deriva el `tenant_id` del JWT
verificado para inyectarlo a services/repositories. Nunca desde el request.
"""

import uuid

from fastapi import Depends

from app.core.dependencies import CurrentUser, get_current_user


async def get_tenant(user: CurrentUser = Depends(get_current_user)) -> uuid.UUID:
    return user.tenant_id
