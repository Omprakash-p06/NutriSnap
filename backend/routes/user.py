"""User Profile Endpoints.

Provides CRUD operations for user profiles with TDEE and macro calculations.
"""

import math

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.schemas.user import UserProfileResponse, UserProfileUpdate

router = APIRouter()


def _calculate_tdee_and_macros(user: User) -> None:
    """Calculate BMI, TDEE, and macro targets in-place on the User model.

    Uses the Mifflin-St Jeor equation for BMR, activity multipliers for TDEE,
    and a standard 30/40/30 macro split (Protein/Carbs/Fats).

    Args:
        user: User model instance to update with computed values.
    """
    if not user.height_cm or not user.weight_kg or not user.age:
        return

    # BMI = weight(kg) / height(m)^2
    height_m = user.height_cm / 100.0
    user.bmi = round(user.weight_kg / (height_m ** 2), 1)

    # Mifflin-St Jeor BMR (male approximation; can be refined later)
    bmr = 10 * user.weight_kg + 6.25 * user.height_cm - 5 * user.age + 5

    # Activity multiplier
    multipliers = {"sedentary": 1.2, "moderate": 1.55, "active": 1.725}
    tdee = bmr * multipliers.get(user.activity_level, 1.55)

    # Goal adjustment (static: lose=-500, gain=+300, maintain=0)
    if user.goal == "lose":
        tdee -= 500
    elif user.goal == "gain":
        tdee += 300

    user.daily_target_kcal = round(tdee)

    # Macro split: 30% Protein (4 kcal/g), 40% Carbs (4 kcal/g), 30% Fats (9 kcal/g)
    user.daily_target_protein_g = round(0.30 * tdee / 4, 1)
    user.daily_target_carbs_g = round(0.40 * tdee / 4, 1)
    user.daily_target_fats_g = round(0.30 * tdee / 9, 1)


@router.get("/profile", response_model=UserProfileResponse)
def get_profile(db: Session = Depends(get_db)) -> User:
    """Get user profile.

    Returns the first user in the database. Creates a default Guest user
    if no users exist.

    Args:
        db: Database session.

    Returns:
        User profile data.
    """
    user = db.query(User).first()
    if not user:
        user = User(name="Guest User")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.put("/profile", response_model=UserProfileResponse)
def update_profile(
    profile: UserProfileUpdate, db: Session = Depends(get_db)
) -> User:
    """Update user profile and recalculate health metrics.

    Accepts partial updates, recalculates BMI/TDEE/macros, and persists.

    Args:
        profile: Updated profile fields.
        db: Database session.

    Returns:
        Updated user profile data.
    """
    user = db.query(User).first()
    if not user:
        user = User(name="Guest User")
        db.add(user)
        db.commit()
        db.refresh(user)

    # Apply only provided fields
    update_data = profile.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    # Recalculate TDEE and macros
    _calculate_tdee_and_macros(user)

    db.commit()
    db.refresh(user)
    return user
