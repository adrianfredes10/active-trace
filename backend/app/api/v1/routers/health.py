from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    database_status = "up"
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() != 1:
            database_status = "down"
    except Exception:
        database_status = "down"

    return HealthResponse(status="ok", database=database_status)
