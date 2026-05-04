"""Meal log CRUD endpoints."""

import json
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.database import get_database
from app.schemas import MealLogCreate, MealLogOut

router = APIRouter(prefix="/logs", tags=["meal-logs"])

# Ensure logs table has the right columns (run on import for safety)
_LOGS_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS meal_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        food_name TEXT,
        calories REAL,
        protein REAL,
        carbs REAL,
        fat REAL,
        mass_g REAL,
        category TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
"""


@router.post("/", response_model=MealLogOut, status_code=201)
async def create_log(
    log: MealLogCreate, current_user: dict = Depends(get_current_user)
):
    """Log a meal for the authenticated user."""
    db = await get_database()
    log_data = log.model_dump()

    query = """
        INSERT INTO meal_logs (user_email, food_name, calories, protein, carbs, fat, mass_g, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        current_user["email"],
        log_data["food_name"],
        log_data["calories"],
        log_data["protein"],
        log_data["carbs"],
        log_data["fat"],
        log_data.get("mass_g", 0),
        log_data.get("category", "Other"),
    )

    cursor = await db.execute(query, params)
    await db.commit()

    async with db.execute("SELECT * FROM meal_logs WHERE id = ?", (cursor.lastrowid,)) as c:
        row = await c.fetchone()
        return dict(row)


@router.get("/", response_model=List[MealLogOut])
async def get_logs(current_user: dict = Depends(get_current_user)):
    """Return the most recent 100 meal logs for the authenticated user."""
    db = await get_database()
    query = "SELECT * FROM meal_logs WHERE user_email = ? ORDER BY timestamp DESC LIMIT 100"

    async with db.execute(query, (current_user["email"],)) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.delete("/{log_id}", status_code=204)
async def delete_log(log_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a meal log by ID (only owner can delete)."""
    db = await get_database()
    cursor = await db.execute(
        "DELETE FROM meal_logs WHERE id = ? AND user_email = ?",
        (log_id, current_user["email"])
    )
    await db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(
            status_code=404, detail="Log not found or not owned by user"
        )


@router.get("/weekly")
async def get_weekly_summary(current_user: dict = Depends(get_current_user)):
    """Get weekly calorie summary for the last 7 days."""
    db = await get_database()
    now = datetime.now(timezone.utc)
    start_of_period = (now - timedelta(days=6)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    query = "SELECT timestamp, calories FROM meal_logs WHERE user_email = ? AND timestamp >= ?"
    async with db.execute(
        query,
        (current_user["email"], start_of_period.strftime("%Y-%m-%d %H:%M:%S"))
    ) as cursor:
        rows = await cursor.fetchall()

    # Group by date
    days = {}
    for i in range(7):
        date = (start_of_period + timedelta(days=i)).date()
        key = date.isoformat()
        label = date.strftime("%a")
        days[key] = {"day": label, "calories": 0}

    for row in rows:
        dt_str = row["timestamp"]
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            continue
        key = dt.date().isoformat()
        if key in days:
            days[key]["calories"] += row["calories"]

    return list(days.values())
