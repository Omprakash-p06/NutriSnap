"""Meal log CRUD endpoints."""

from datetime import datetime, timedelta, timezone
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.database import get_database
from app.schemas import MealLogCreate, MealLogOut

router = APIRouter(prefix="/logs", tags=["meal-logs"])


@router.post("/", response_model=MealLogOut, status_code=201)
async def create_log(
    log: MealLogCreate, current_user: dict = Depends(get_current_user)
):
    """Log a meal for the authenticated user."""
    db = await get_database()
    doc = {
        **log.model_dump(),
        "user_id": str(current_user["_id"]),
        "logged_at": datetime.now(timezone.utc),
    }
    result = await db.meal_logs.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


@router.get("/", response_model=List[MealLogOut])
async def get_logs(current_user: dict = Depends(get_current_user)):
    """Return the most recent 100 meal logs for the authenticated user."""
    db = await get_database()
    logs = (
        await db.meal_logs.find({"user_id": str(current_user["_id"])})
        .sort("logged_at", -1)
        .to_list(100)
    )
    for log in logs:
        log["_id"] = str(log["_id"])
    return logs


@router.delete("/{log_id}", status_code=204)
async def delete_log(log_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a meal log by ID (only owner can delete)."""
    db = await get_database()
    try:
        result = await db.meal_logs.delete_one(
            {"_id": ObjectId(log_id), "user_id": str(current_user["_id"])}
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid log ID")

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404, detail="Log not found or not owned by user"
        )


@router.get("/weekly")
async def get_weekly_summary(current_user: dict = Depends(get_current_user)):
    """Get weekly calorie summary for the last 7 days."""
    db = await get_database()
    now = datetime.now(timezone.utc)
    # Start of day 6 days ago (total 7 days including today)
    start_of_period = (now - timedelta(days=6)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    logs = await db.meal_logs.find(
        {"user_id": str(current_user["_id"]), "logged_at": {"$gte": start_of_period}}
    ).to_list(1000)

    # Group by date
    days = {}
    for i in range(7):
        date = (start_of_period + timedelta(days=i)).date()
        key = date.isoformat()
        label = date.strftime("%a")
        days[key] = {"day": label, "calories": 0}

    for log in logs:
        key = log["logged_at"].date().isoformat()
        if key in days:
            days[key]["calories"] += log["calories"]

    return list(days.values())
