"""Meal planning and daily summary endpoints."""

from datetime import datetime, timezone

from app.auth import get_current_user
from app.database import get_database
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/planning", tags=["planning"])


@router.get("/daily-summary")
async def daily_summary(current_user: dict = Depends(get_current_user)):
    """Aggregate today's logged meals into calorie and macro totals."""
    db = await get_database()
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    logs = await db.meal_logs.find(
        {"user_id": str(current_user["_id"]), "logged_at": {"$gte": today_start}}
    ).to_list(500)

    return {
        "date": today_start.date().isoformat(),
        "calories": round(sum(log.get("calories", 0) for log in logs), 1),
        "protein": round(sum(log.get("protein", 0) for log in logs), 1),
        "carbs": round(sum(log.get("carbs", 0) for log in logs), 1),
        "fat": round(sum(log.get("fat", 0) for log in logs), 1),
        "meals_logged": len(logs),
    }


@router.get("/weekly-summary")
async def weekly_summary(current_user: dict = Depends(get_current_user)):
    """Return daily calorie totals for the last 7 days."""
    from datetime import timedelta

    db = await get_database()
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    result = []
    for i in range(7):
        day_start = today - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        logs = await db.meal_logs.find(
            {
                "user_id": str(current_user["_id"]),
                "logged_at": {"$gte": day_start, "$lt": day_end},
            }
        ).to_list(500)
        result.append(
            {
                "date": day_start.date().isoformat(),
                "calories": round(sum(log.get("calories", 0) for log in logs), 1),
            }
        )
    return list(reversed(result))
