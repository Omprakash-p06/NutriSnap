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
