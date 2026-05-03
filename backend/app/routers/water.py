from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.database import get_database
from app.schemas import WaterLogCreate, WaterLogOut

router = APIRouter(prefix="/water", tags=["water"])


@router.post("/", response_model=WaterLogOut, status_code=201)
async def log_water(
    log: WaterLogCreate, current_user: dict = Depends(get_current_user)
):
    """Log water intake for the authenticated user."""
    db = await get_database()
    doc = {
        **log.model_dump(),
        "user_id": str(current_user["_id"]),
        "timestamp": datetime.now(timezone.utc),
    }
    result = await db.water_logs.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


@router.get("/today")
async def get_today_water(current_user: dict = Depends(get_current_user)):
    """Get total water intake for today."""
    db = await get_database()
    # Use naive UTC for start of day to match MongoDB storage if it's stored as UTC
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    logs = await db.water_logs.find(
        {"user_id": str(current_user["_id"]), "timestamp": {"$gte": start_of_day}}
    ).to_list(1000)

    total = sum(log["amount"] for log in logs)
    return {"total": total}
