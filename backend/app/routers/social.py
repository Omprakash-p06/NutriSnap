from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.database import get_database
from app.schemas import PostCreate, PostOut

router = APIRouter(prefix="/posts", tags=["social"])


@router.get("/", response_model=List[PostOut])
async def get_posts(current_user: dict = Depends(get_current_user)):
    """Fetch the community feed."""
    db = await get_database()
    posts = await db.posts.find().sort("timestamp", -1).limit(20).to_list(20)
    for post in posts:
        post["_id"] = str(post["_id"])

    if not posts:
        # Mock Feed if empty
        return [
            {
                "_id": "1",
                "userName": "Alex Fit",
                "user_id": "mock_1",
                "mealName": "Quinoa Power Bowl",
                "calories": 450,
                "imageUrl": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=200",
                "likes": 12,
                "timestamp": datetime.now(timezone.utc),
            },
            {
                "_id": "2",
                "userName": "Sarah Healthy",
                "user_id": "mock_2",
                "mealName": "Avocado Toast",
                "calories": 320,
                "imageUrl": "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=200",
                "likes": 8,
                "timestamp": datetime.now(timezone.utc),
            },
        ]
    return posts


@router.post("/", response_model=PostOut, status_code=201)
async def create_post(post: PostCreate, current_user: dict = Depends(get_current_user)):
    """Share a meal to the community feed."""
    db = await get_database()
    doc = {
        **post.model_dump(),
        "user_id": str(current_user["_id"]),
        "likes": 0,
        "timestamp": datetime.now(timezone.utc),
    }
    result = await db.posts.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc
