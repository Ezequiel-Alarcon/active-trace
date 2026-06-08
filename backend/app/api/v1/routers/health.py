from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db

router = APIRouter(prefix="/health")


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    db_status = "up"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "down"
    return {"status": "ok", "database": db_status}