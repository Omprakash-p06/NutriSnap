"""Food search and database endpoints."""
import json
from pathlib import Path
from fastapi import APIRouter, Query

router = APIRouter(prefix="/food", tags=["food"])

# Load local food database at startup
_db_path = Path(__file__).parent.parent.parent / "data" / "food_database.json"
try:
    with _db_path.open(encoding="utf-8") as f:
        FOOD_DB: list[dict] = json.load(f)
except FileNotFoundError:
    FOOD_DB = []


@router.get("/search")
async def search_food(q: str = Query(..., min_length=2, description="Food name to search")):
    """Search local food database by name (case-insensitive)."""
    q_lower = q.lower()
    results = [item for item in FOOD_DB if q_lower in item["name"].lower()]
    return results[:20]


@router.get("/database")
async def list_foods(skip: int = 0, limit: int = 50):
    """Return a paginated list of all foods in the database."""
    return {"total": len(FOOD_DB), "items": FOOD_DB[skip : skip + limit]}
