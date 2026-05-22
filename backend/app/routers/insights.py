"""Insights endpoint — real data-driven nutrition coaching."""

from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.database import get_database
from app.schemas import InsightOut

router = APIRouter(prefix="/insights", tags=["insights"])


async def _get_recent_logs(db, user_email: str, days: int = 7) -> list:
    """Return meal logs for the last *days* days."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    query = """
        SELECT calories, protein, carbs, fat, timestamp
        FROM meal_logs
        WHERE user_email = ? AND timestamp >= ?
        ORDER BY timestamp DESC
    """
    async with db.execute(query, (user_email, since)) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def _get_user_settings(db, user_email: str) -> dict:
    """Return user profile and settings."""
    async with db.execute(
        "SELECT settings, weight_kg, height_cm, age, goal, activity_level FROM users WHERE email = ?",
        (user_email,),
    ) as cur:
        row = await cur.fetchone()
    if not row:
        return {}
    import json

    data = dict(row)
    raw = data.pop("settings", None)
    settings = json.loads(raw) if raw else {}
    data.update(settings)
    return data


async def _get_today_water(db, user_email: str) -> int:
    """Return total water logged today in ml."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    async with db.execute(
        "SELECT SUM(amount_ml) as total FROM water_logs WHERE user_email = ? AND DATE(timestamp) = ?",
        (user_email, today),
    ) as cur:
        row = await cur.fetchone()
    total = row["total"] if row and row["total"] else 0
    return int(total)


def _group_by_date(logs: list) -> dict:
    """Aggregate logs by date string."""
    days: dict = {}
    for r in logs:
        dt_str = r.get("timestamp", "")
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            continue
        key = dt.date().isoformat()
        if key not in days:
            days[key] = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0, "entries": 0}
        days[key]["calories"] += r.get("calories") or 0
        days[key]["protein"] += r.get("protein") or 0
        days[key]["carbs"] += r.get("carbs") or 0
        days[key]["fat"] += r.get("fat") or 0
        days[key]["entries"] += 1
    return days


def _generate_insights(
    logs: list, user_settings: dict, water_ml: int
) -> list[dict]:
    """Derive up to 5 personalized insights from real data."""

    insights: list[dict] = []

    # Pull goals from settings (with sensible defaults)
    calorie_goal = float(user_settings.get("dailyCalorieGoal", 2000))
    protein_goal = float(user_settings.get("proteinGoal", 150))
    goal_type = user_settings.get("goal", "maintenance")

    days = _group_by_date(logs)
    today_str = datetime.now(timezone.utc).date().isoformat()
    today = days.get(today_str, {})
    today_cals = today.get("calories", 0)
    today_protein = today.get("protein", 0)
    today_entries = today.get("entries", 0)

    # ── 1. Today's calorie progress ──────────────────────────────────────────
    if today_cals > 0:
        pct = (today_cals / calorie_goal) * 100 if calorie_goal else 0
        if pct < 50:
            insights.append(
                {
                    "title": "Low Calorie Intake Today",
                    "message": (
                        f"You've only logged {int(today_cals)} kcal — "
                        f"less than half your {int(calorie_goal)} kcal goal. "
                        "Ensure you're not skipping meals."
                    ),
                    "type": "warning",
                }
            )
        elif pct <= 110:
            insights.append(
                {
                    "title": "Calories on Track! 🎯",
                    "message": (
                        f"You've logged {int(today_cals)} kcal out of "
                        f"your {int(calorie_goal)} kcal goal ({int(pct)}%). Great work!"
                    ),
                    "type": "success",
                }
            )
        else:
            insights.append(
                {
                    "title": "Calorie Budget Exceeded",
                    "message": (
                        f"You've consumed {int(today_cals)} kcal — "
                        f"{int(today_cals - calorie_goal)} kcal over your daily goal. "
                        "Consider a lighter dinner."
                    ),
                    "type": "warning",
                }
            )

    # ── 2. Protein goal tracking ─────────────────────────────────────────────
    if today_protein > 0 or today_entries > 0:
        if today_protein >= protein_goal * 0.8:
            insights.append(
                {
                    "title": "Protein Goal Nearly Met 💪",
                    "message": (
                        f"You've hit {int(today_protein)}g of protein "
                        f"(goal: {int(protein_goal)}g). Your muscles will thank you!"
                    ),
                    "type": "success",
                }
            )
        else:
            remaining = max(0, protein_goal - today_protein)
            insights.append(
                {
                    "title": "Boost Your Protein",
                    "message": (
                        f"You're {int(remaining)}g short of your {int(protein_goal)}g "
                        "protein goal. Try adding chicken, eggs, or Greek yogurt."
                    ),
                    "type": "info",
                }
            )

    # ── 3. Weekly consistency streak ─────────────────────────────────────────
    if len(days) >= 1:
        logged_days = len(days)
        if logged_days >= 5:
            insights.append(
                {
                    "title": f"{logged_days}-Day Logging Streak 🔥",
                    "message": (
                        f"You've tracked meals on {logged_days} of the last 7 days. "
                        "Consistency is the biggest predictor of success!"
                    ),
                    "type": "success",
                }
            )
        elif logged_days <= 2:
            insights.append(
                {
                    "title": "Build Your Logging Habit",
                    "message": (
                        f"You've only logged on {logged_days} day(s) this week. "
                        "Try logging every meal — even estimates help!"
                    ),
                    "type": "warning",
                }
            )

    # ── 4. Hydration status ───────────────────────────────────────────────────
    hydration_goal = 2000  # ml
    if water_ml >= hydration_goal:
        insights.append(
            {
                "title": "Hydration Goal Reached 💧",
                "message": (
                    f"You've had {water_ml}ml of water today — "
                    "well above your 2L target. Keep it up!"
                ),
                "type": "success",
            }
        )
    elif water_ml > 0:
        needed = hydration_goal - water_ml
        insights.append(
            {
                "title": "Stay Hydrated",
                "message": (
                    f"You've logged {water_ml}ml so far. "
                    f"Drink {needed}ml more to hit your 2L daily target."
                ),
                "type": "info",
            }
        )
    else:
        insights.append(
            {
                "title": "Hydration Tip 💧",
                "message": (
                    "Drinking 250ml of water right after waking up can boost "
                    "your metabolism by up to 24%. Start logging your water intake!"
                ),
                "type": "info",
            }
        )

    # ── 5. Weekly average vs. goal ────────────────────────────────────────────
    if len(days) >= 3:
        avg_cals = sum(d["calories"] for d in days.values()) / len(days)
        diff = avg_cals - calorie_goal
        if abs(diff) > 200:
            direction = "above" if diff > 0 else "below"
            tips = (
                "Consider reducing portion sizes."
                if diff > 0
                else "Make sure you're eating enough to fuel your body."
            )
            insights.append(
                {
                    "title": f"Weekly Average {direction.capitalize()} Goal",
                    "message": (
                        f"Your 7-day average is {int(avg_cals)} kcal — "
                        f"{int(abs(diff))} kcal {direction} your {int(calorie_goal)} kcal target. "
                        f"{tips}"
                    ),
                    "type": "warning" if abs(diff) > 300 else "info",
                }
            )

    # ── Fallback ─────────────────────────────────────────────────────────────
    if not insights:
        insights.append(
            {
                "title": "Start Logging Your Meals",
                "message": (
                    "Scan or search for your first meal to unlock "
                    "personalized nutrition insights!"
                ),
                "type": "info",
            }
        )

    return insights[:5]  # Cap at 5 cards


@router.get("/", response_model=List[InsightOut])
async def get_insights(current_user: dict = Depends(get_current_user)):
    """Generate real, data-driven nutrition insights from the user's logs."""
    db = await get_database()
    user_email = current_user["email"]

    logs = await _get_recent_logs(db, user_email, days=7)
    user_settings = await _get_user_settings(db, user_email)
    water_ml = await _get_today_water(db, user_email)

    return _generate_insights(logs, user_settings, water_ml)
