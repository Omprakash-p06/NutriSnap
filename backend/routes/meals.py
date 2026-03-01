"""Meal Logging Endpoints.

CRUD operations for meal logging and history.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.food_item import FoodItem
from backend.models.meal import Meal
from backend.schemas.meal import MealCreate, MealResponse, MealUpdate

router = APIRouter()


@router.post("/meals", response_model=MealResponse)
async def create_meal(
    meal_data: MealCreate,
    db: Session = Depends(get_db),
) -> MealResponse:
    """Create a new meal log entry.

    Args:
        meal_data: Meal creation data.
        db: Database session.

    Returns:
        Created meal response.
    """
    # Create meal record
    meal = Meal(
        user_id=meal_data.user_id or 1,  # Default user for demo
        image_url=meal_data.image_url,
        total_calories=meal_data.total_calories,
        total_protein=meal_data.total_protein,
        total_carbs=meal_data.total_carbs,
        total_fats=meal_data.total_fats,
        logged_at=datetime.utcnow(),
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)

    # Create food items
    for item in meal_data.food_items:
        food_item = FoodItem(
            meal_id=meal.id,
            food_class=item.food_class,
            confidence=item.confidence,
            ai_portion_grams=item.ai_portion_grams,
            user_portion_grams=item.user_portion_grams or item.ai_portion_grams,
            calories=item.calories,
            protein=item.protein,
            carbs=item.carbs,
            fats=item.fats,
        )
        db.add(food_item)

    db.commit()
    db.refresh(meal)

    return MealResponse.model_validate(meal)


@router.get("/meals", response_model=List[MealResponse])
async def get_meals(
    user_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> List[MealResponse]:
    """Get meal history.

    Args:
        user_id: Filter by user ID.
        limit: Maximum number of meals to return.
        offset: Number of meals to skip.
        db: Database session.

    Returns:
        List of meal responses.
    """
    query = db.query(Meal).order_by(Meal.logged_at.desc())

    if user_id:
        query = query.filter(Meal.user_id == user_id)

    meals = query.offset(offset).limit(limit).all()
    return [MealResponse.model_validate(meal) for meal in meals]


@router.get("/meals/{meal_id}", response_model=MealResponse)
async def get_meal(
    meal_id: int,
    db: Session = Depends(get_db),
) -> MealResponse:
    """Get a specific meal by ID.

    Args:
        meal_id: Meal ID.
        db: Database session.

    Returns:
        Meal response.

    Raises:
        HTTPException: If meal not found.
    """
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    return MealResponse.model_validate(meal)


@router.put("/meals/{meal_id}", response_model=MealResponse)
async def update_meal(
    meal_id: int,
    meal_data: MealUpdate,
    db: Session = Depends(get_db),
) -> MealResponse:
    """Update a meal entry.

    Args:
        meal_id: Meal ID to update.
        meal_data: Updated meal data.
        db: Database session.

    Returns:
        Updated meal response.

    Raises:
        HTTPException: If meal not found.
    """
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    # Update fields if provided
    update_data = meal_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meal, field, value)

    db.commit()
    db.refresh(meal)
    return MealResponse.model_validate(meal)


@router.delete("/meals/{meal_id}")
async def delete_meal(
    meal_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Delete a meal entry.

    Args:
        meal_id: Meal ID to delete.
        db: Database session.

    Returns:
        Success message.

    Raises:
        HTTPException: If meal not found.
    """
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    # Delete associated food items
    db.query(FoodItem).filter(FoodItem.meal_id == meal_id).delete()
    db.delete(meal)
    db.commit()

    return {"message": "Meal deleted successfully"}
