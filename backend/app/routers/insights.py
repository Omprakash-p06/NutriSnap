from typing import List

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.schemas import InsightOut

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/", response_model=List[InsightOut])
async def get_insights(current_user: dict = Depends(get_current_user)):
    """Generate AI-powered nutrition insights for the user."""
    # In a real app, this would query the user's logs and use an LLM or rules engine.
    # For now, we migrate the logic from the Node.js server.
    insights = [
        {
            "title": "Calories on Track!",
            "message": "You've stayed within 10% of your calorie goal for 3 days. Keep it up!",
            "type": "success",
        },
        {
            "title": "Hydration Boost",
            "message": "Drinking 250ml of water right after waking up can boost your metabolism by 24%.",
            "type": "info",
        },
        {
            "title": "Muscle Recovery",
            "message": "Your protein intake was a bit low yesterday. Consider adding Greek yogurt or eggs today.",
            "type": "warning",
        },
    ]
    return insights
