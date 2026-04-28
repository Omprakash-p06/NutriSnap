"""Meal log CRUD endpoints."""

from datetime import datetime, timezone
from typing import List

from app.auth import get_current_user
from app.database import get_database
from app.schemas import MealLogCreate, MealLogOut
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

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
