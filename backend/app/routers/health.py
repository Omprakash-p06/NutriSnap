"""Health-check and liveness probe endpoints."""

from fastapi import APIRouter

from app.database import get_database

router = APIRouter(prefix="/health", tags=["monitoring"])


@router.get("/")
async def health_check():
    return {"status": "ok", "service": "NutriSnap API v1.0"}


@router.get("/db")
async def db_health():
    """Ping MongoDB and report connectivity."""
    try:
        db = await get_database()
        await db.command("ping")
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        return {"status": "error", "database": str(exc)}
