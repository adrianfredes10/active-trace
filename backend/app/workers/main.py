"""Worker de cola de comunicaciones — C-12."""

import asyncio
import logging

from app.core.config import get_settings
from app.core.database import dispose_db, get_session_factory, init_db
from app.workers.comunicacion_worker import procesar_pendientes

logger = logging.getLogger(__name__)
_POLL_SECONDS = 15


async def run() -> None:
    settings = get_settings()
    init_db(settings.database_url)
    logger.info("Worker de comunicaciones iniciado")
    factory = get_session_factory()
    try:
        while True:
            async with factory() as session:
                from sqlalchemy import select

                from app.models.tenant import Tenant

                tenants = (
                    await session.execute(
                        select(Tenant.id).where(Tenant.deleted_at.is_(None))
                    )
                ).scalars().all()
                for tenant_id in tenants:
                    await procesar_pendientes(session, tenant_id)
                    await session.commit()
            await asyncio.sleep(_POLL_SECONDS)
    finally:
        await dispose_db()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())


if __name__ == "__main__":
    main()
