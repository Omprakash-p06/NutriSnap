"""Dashboard Statistics Endpoints.

Provides daily and weekly nutrition summaries.
"""

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models.meal import Meal
from backend.schemas.nutrition import DailyStats, WeeklyTrend

router = APIRouter()


@router.get("/dashboard/stats", response_model=DailyStats)
async def get_daily_stats(
    user_id: int = 1,
    db: Session = Depends(get_db),
) -> DailyStats:
    """Get daily nutrition statistics.

    Args:
        user_id: User ID.
        db: Database session.

    Returns:
        Daily statistics including calories and macros.
    """
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    # Query today's meals
    result = (
        db.query(
            func.sum(Meal.total_calories).label("calories"),
            func.sum(Meal.total_protein).label("protein"),
            func.sum(Meal.total_carbs).label("carbs"),
            func.sum(Meal.total_fats).label("fats"),
            func.count(Meal.id).label("meal_count"),  # pylint: disable=not-callable
        )
        .filter(
            Meal.user_id == user_id,
            Meal.logged_at >= today_start,
            Meal.logged_at <= today_end,
        )
        .first()
    )

    target = settings.default_daily_target
    consumed = result.calories or 0

    return DailyStats(
        date=today.isoformat(),
        calories_consumed=round(consumed, 1),
        calories_target=target,
        calories_remaining=max(0, target - consumed),
        protein=round(result.protein or 0, 1),
        carbs=round(result.carbs or 0, 1),
        fats=round(result.fats or 0, 1),
        meal_count=result.meal_count or 0,
    )


@router.get("/dashboard/weekly", response_model=List[WeeklyTrend])
async def get_weekly_trend(
    user_id: int = 1,
    db: Session = Depends(get_db),
) -> List[WeeklyTrend]:
    """Get weekly calorie trend for the last 7 days.

    Args:
        user_id: User ID.
        db: Database session.

    Returns:
        List of daily calorie totals for the past week.
    """
    today = datetime.utcnow().date()
    week_data: List[WeeklyTrend] = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())

        result = (
            db.query(
                func.sum(Meal.total_calories).label("calories"),
            )
            .filter(
                Meal.user_id == user_id,
                Meal.logged_at >= day_start,
                Meal.logged_at <= day_end,
            )
            .first()
        )

        week_data.append(
            WeeklyTrend(
                date=day.isoformat(),
                day_name=day.strftime("%a"),
                calories=round(result.calories or 0, 1),
            )
        )

    return week_data
