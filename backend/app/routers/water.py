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
    amount = log.amount
    
    query = "INSERT INTO water_logs (user_email, amount_ml) VALUES (?, ?)"
    cursor = await db.execute(query, (current_user["email"], amount))
    await db.commit()
    
    async with db.execute("SELECT * FROM water_logs WHERE id = ?", (cursor.lastrowid,)) as cursor:
        row = await cursor.fetchone()
        return dict(row)


@router.get("/today")
async def get_today_water(current_user: dict = Depends(get_current_user)):
    """Get total water intake for today."""
    db = await get_database()
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    query = "SELECT SUM(amount_ml) as total FROM water_logs WHERE user_email = ? AND timestamp >= ?"
    async with db.execute(query, (current_user["email"], start_of_day.strftime("%Y-%m-%d %H:%M:%S"))) as cursor:
        row = await cursor.fetchone()
        total = row["total"] or 0
    
    return {"total": total}

