"""Authentication endpoints — signup and login."""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timezone

from app.database import get_database
from app.auth import get_password_hash, verify_password, create_access_token
from app.schemas import UserCreate, UserOut, Token

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=UserOut, status_code=201)
async def signup(user_data: UserCreate):
    """Register a new user account."""
    db = await get_database()
    if await db.users.find_one({"email": user_data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    doc = {
        **user_data.model_dump(exclude={"password"}),
        "hashed_password": get_password_hash(user_data.password),
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate and return a JWT access token."""
    db = await get_database()
    user = await db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer"}
