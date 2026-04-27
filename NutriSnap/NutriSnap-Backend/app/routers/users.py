"""User profile CRUD and personalised nutrition targets."""
from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user, get_password_hash
from app.database import get_database
from app.schemas import UserOut, UserUpdate
from app.utils.nutrition import calculate_bmr, calculate_tdee, adjust_for_goal, macros_from_calories

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_profile(current_user: dict = Depends(get_current_user)):
    current_user["_id"] = str(current_user["_id"])
    return current_user


@router.put("/me", response_model=UserOut)
async def update_profile(
    update: UserUpdate, current_user: dict = Depends(get_current_user)
):
    db = await get_database()
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    await db.users.update_one({"email": current_user["email"]}, {"$set": update_data})
    updated = await db.users.find_one({"email": current_user["email"]})
    updated["_id"] = str(updated["_id"])
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
