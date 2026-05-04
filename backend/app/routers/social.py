from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.database import get_database
from app.schemas import PostCreate, PostOut

router = APIRouter(prefix="/social", tags=["social"])



@router.get("/posts", response_model=List[PostOut])
async def get_posts(current_user: dict = Depends(get_current_user)):
    """Fetch the community feed."""
    db = await get_database()
    query = "SELECT * FROM social_posts ORDER BY timestamp DESC LIMIT 20"
    
    async with db.execute(query) as cursor:
        rows = await cursor.fetchall()
        posts = []
        for row in rows:
            doc = dict(row)
            posts.append({
                "_id": str(doc["id"]),
                "user_id": doc["user_email"],
                "userName": doc["user_name"],
                "mealName": doc["meal_name"],
                "calories": doc["calories"],
                "imageUrl": doc["image_url"],
                "likes": doc["likes_count"],
                "timestamp": doc["timestamp"]
            })
        
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


@router.post("/posts", response_model=PostOut, status_code=201)
async def create_post(post: PostCreate, current_user: dict = Depends(get_current_user)):
    """Share a meal to the community feed."""
    db = await get_database()
    post_data = post.model_dump()
    
    query = """
        INSERT INTO social_posts (user_email, user_name, meal_name, calories, image_url, likes_count)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    params = (
        current_user["email"],
        post_data["userName"],
        post_data["mealName"],
        post_data["calories"],
        post_data["imageUrl"],
        0
    )
    
    cursor = await db.execute(query, params)
    await db.commit()
    
    return {
        "_id": str(cursor.lastrowid),
        "user_id": current_user["email"],
        **post_data,
        "likes": 0,
        "timestamp": datetime.now(timezone.utc)
    }

