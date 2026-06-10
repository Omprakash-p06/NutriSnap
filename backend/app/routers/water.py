from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

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

    async with db.execute(
        "SELECT id, user_email, amount_ml as amount, timestamp FROM water_logs WHERE id = ?",
        (cursor.lastrowid,),
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row)


@router.get("/today")
async def get_today_water(current_user: dict = Depends(get_current_user)):
    """Get total water intake for today."""
    db = await get_database()
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    query = "SELECT SUM(amount_ml) as total FROM water_logs WHERE user_email = ? AND timestamp >= ?"
    async with db.execute(
        query, (current_user["email"], start_of_day.strftime("%Y-%m-%d %H:%M:%S"))
    ) as cursor:
        row = await cursor.fetchone()
        total = row["total"] or 0

    return {"total": total}


@router.get("/today/logs")
async def get_today_water_logs(current_user: dict = Depends(get_current_user)):
    """Get today's water log entries for the authenticated user."""
    db = await get_database()
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    query = """
        SELECT id, amount_ml as amount, timestamp
        FROM water_logs
        WHERE user_email = ? AND timestamp >= ?
        ORDER BY timestamp DESC
    """
    async with db.execute(
        query,
        (current_user["email"], start_of_day.strftime("%Y-%m-%d %H:%M:%S")),
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.delete("/{log_id}", status_code=204)
async def delete_water_log(log_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a water log by ID for the authenticated user."""
    db = await get_database()
    cursor = await db.execute(
        "DELETE FROM water_logs WHERE id = ? AND user_email = ?",
        (log_id, current_user["email"]),
    )
    await db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Water log not found")
