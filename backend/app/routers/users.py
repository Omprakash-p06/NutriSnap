"""User profile CRUD and personalised nutrition targets."""

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user, get_password_hash
from app.database import get_database
from app.schemas import UserOut, UserUpdate
from app.utils.nutrition import (
    adjust_for_goal,
    calculate_bmr,
    calculate_tdee,
    macros_from_calories,
)

router = APIRouter(prefix="/users", tags=["users"])


import json

@router.get("/me", response_model=UserOut)
async def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
async def update_profile(
    update: UserUpdate, current_user: dict = Depends(get_current_user)
):
    db = await get_database()
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    if not update_data:
        return current_user

    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    if "settings" in update_data:
        update_data["settings"] = json.dumps(update_data["settings"])

    # Build dynamic SQL update
    fields = ", ".join([f"{k} = ?" for k in update_data.keys()])
    values = list(update_data.values())
    values.append(current_user["email"])
    
    query = f"UPDATE users SET {fields} WHERE email = ?"
    await db.execute(query, tuple(values))
    await db.commit()
    
    # Retrieve updated user
    async with db.execute("SELECT * FROM users WHERE email = ?", (current_user["email"],)) as cursor:
        row = await cursor.fetchone()
        updated = dict(row)
        if updated.get("settings"):
            updated["settings"] = json.loads(updated["settings"])
        return updated



@router.get("/me/targets")
async def get_targets(current_user: dict = Depends(get_current_user)):
    """Calculate personalised daily calorie and macro targets."""
    required = ["weight_kg", "height_cm", "age", "gender", "activity_level", "goal"]
    missing = [f for f in required if not current_user.get(f)]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Complete your profile first. Missing fields: {missing}",
        )

    bmr = calculate_bmr(
        current_user["weight_kg"],
        current_user["height_cm"],
        current_user["age"],
        current_user["gender"],
    )
    tdee = calculate_tdee(bmr, current_user["activity_level"])
    target_calories = adjust_for_goal(tdee, current_user["goal"])
    macros = macros_from_calories(target_calories)

    return {
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1),
        "target_calories": round(target_calories, 1),
        **macros,
    }


from pydantic import BaseModel
from typing import Optional

class GenerateTargetsRequest(BaseModel):
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    activity_level: Optional[str] = None
    goal: Optional[str] = None


@router.post("/generate-targets")
async def generate_targets(
    request: GenerateTargetsRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate daily calorie and macro goals via LLM or formula fallback."""
    weight = request.weight_kg or 70.0
    height = request.height_cm or 170.0
    age = request.age or 30
    gender = request.gender or "male"
    activity_level = request.activity_level or "1.55"
    goal = request.goal or "maintain"

    prompt = f"""
    Calculate personalized daily nutrition targets (Calorie, Protein, Carbs, and Fat) for a user with the following physical attributes and goals:
    
    Attributes:
    - Weight: {weight} kg
    - Height: {height} cm
    - Age: {age} years old
    - Gender: {gender}
    - Activity Level: {activity_level} (activity multiplier)
    - Goal: {goal}
    
    Instructions:
    1. If any attribute is missing or typical adult values were used, assume sensible/healthy defaults and mention these assumptions in the explanation.
    2. Use scientifically-backed formulas (like Mifflin-St Jeor for BMR, adjusted by activity level and nutrition goal) to estimate:
       - Daily Calorie Target (kcal)
       - Protein (g) (typically 1.6-2.2g per kg of body weight, or 15-25% of calories)
       - Carbs (g) (typically 45-65% of calories)
       - Fat (g) (typically 20-35% of calories)
    3. Ensure the macronutrient calories add up approximately to the total daily calorie target (1g protein = 4 kcal, 1g carb = 4 kcal, 1g fat = 9 kcal).
    
    Response format:
    You MUST respond with a JSON object containing exactly the following keys:
    {{
      "dailyCalorieGoal": <int>,
      "proteinGoal": <int>,
      "carbsGoal": <int>,
      "fatGoal": <int>,
      "reasoning": "<string: a concise 1-2 sentence explanation of your assumptions and scientific reasoning behind these values>"
    }}
    Do not output any markdown formatting, pre-amble, or post-amble outside of the JSON object.
    """

    try:
        from nutrisnap.verification.llm_service import LLMService
        import os
        from loguru import logger

        llm = LLMService(provider=os.getenv("LLM_PROVIDER", "gemini"))
        if llm.is_available:
            result = await llm.generate_json(prompt)
            if isinstance(result, dict) and all(k in result for k in ("dailyCalorieGoal", "proteinGoal", "carbsGoal", "fatGoal")):
                return {
                    "dailyCalorieGoal": int(result["dailyCalorieGoal"]),
                    "proteinGoal": int(result["proteinGoal"]),
                    "carbsGoal": int(result["carbsGoal"]),
                    "fatGoal": int(result["fatGoal"]),
                    "reasoning": result.get("reasoning", "Calculated by Google Gemini based on your physical attributes and goals.")
                }
    except Exception as exc:
        from loguru import logger
        logger.warning(f"LLM target generation failed: {exc}. Falling back to Mifflin-St Jeor formula.")

    # Python Fallback
    w = float(weight)
    h = float(height)
    a = int(age)
    sex = str(gender).lower()
    
    # parse activity level
    act_str = str(activity_level).lower()
    if "sedentary" in act_str or "1.2" in act_str: act = 1.2
    elif "light" in act_str or "1.375" in act_str: act = 1.375
    elif "moderate" in act_str or "1.55" in act_str: act = 1.55
    elif "active" in act_str or "1.725" in act_str: act = 1.725
    elif "very" in act_str or "1.9" in act_str: act = 1.9
    else:
        try:
            act = float(act_str)
        except ValueError:
            act = 1.55
            
    # parse goal
    goal_str = str(goal).lower()
    if "loss" in goal_str or "lose" in goal_str:
        goal_type = "lose"
    elif "gain" in goal_str or "muscle" in goal_str:
        goal_type = "gain"
    else:
        goal_type = "maintain"
    
    # BMR Mifflin-St Jeor
    bmr = 10 * w + 6.25 * h - 5 * a + (5 if sex == "male" else -161)
    tdee = bmr * act
    target_cal = tdee
    if goal_type == "lose":
        target_cal -= 500
    elif goal_type == "gain":
        target_cal += 300
    
    dailyCalorieGoal = round(target_cal)
    proteinGoal = round(w * 1.6)
    carbsGoal = round((target_cal * 0.45) / 4)
    fatGoal = round((target_cal * 0.3) / 9)
    
    reasoning = (
        f"Calculated BMR ({round(bmr)} kcal) via Mifflin-St Jeor, "
        f"scaled by activity level ({act}x) and adjusted for your goal (fallback)."
    )
    
    return {
        "dailyCalorieGoal": dailyCalorieGoal,
        "proteinGoal": proteinGoal,
        "carbsGoal": carbsGoal,
        "fatGoal": fatGoal,
        "reasoning": reasoning
    }

