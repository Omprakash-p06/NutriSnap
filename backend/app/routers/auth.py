"""Authentication endpoints — signup and login."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import create_access_token, get_password_hash, verify_password
from app.database import get_database
from app.schemas import UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["authentication"])

from typing import Optional

from pydantic import BaseModel


class UserLoginProfile(BaseModel):
    id: int
    email: str
    full_name: str
    xp: int
    level: int
    settings: Optional[dict] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    activity_level: Optional[str] = None
    goal: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserLoginProfile


@router.post("/signup", response_model=UserOut, status_code=201)
async def signup(user_data: UserCreate):
    """Register a new user account."""
    db = await get_database()

    async with db.execute(
        "SELECT * FROM users WHERE email = ?", (user_data.email,)
    ) as cursor:
        if await cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

    query = """
        INSERT INTO users (email, full_name, hashed_password)
        VALUES (?, ?, ?)
    """
    params = (
        user_data.email,
        user_data.full_name,
        get_password_hash(user_data.password),
    )

    cursor = await db.execute(query, params)
    await db.commit()

    return {
        "_id": str(cursor.lastrowid),
        "email": user_data.email,
        "full_name": user_data.full_name,
        "created_at": datetime.now(timezone.utc),
    }


@router.post("/login", response_model=LoginResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate and return a JWT access token along with user profile."""
    db = await get_database()

    async with db.execute(
        "SELECT * FROM users WHERE email = ?", (form_data.username,)
    ) as cursor:
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        user = dict(row)

    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": user["email"]})

    # Format user profile for response
    user_profile = {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "xp": user["xp"],
        "level": user["level"],
        "weight_kg": user["weight_kg"],
        "height_cm": user["height_cm"],
        "age": user["age"],
        "gender": user["gender"],
        "activity_level": user["activity_level"],
        "goal": user["goal"],
    }

    if user.get("settings"):
        user_profile["settings"] = json.loads(user["settings"])

    return {"access_token": token, "token_type": "bearer", "user": user_profile}


@router.get("/guest", response_model=LoginResponse)
async def guest_login():
    """Issue a real JWT for the pre-seeded guest user (no password required).

    This allows the demo app to access all protected endpoints without
    requiring the user to sign up. The guest account is created at DB
    init time with realistic profile data.
    """
    db = await get_database()
    async with db.execute(
        "SELECT * FROM users WHERE email = 'guest@nutrisnap.ai'"
    ) as cursor:
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Guest user not seeded yet — restart the server",
        )

    user = dict(row)
    token = create_access_token({"sub": user["email"]})

    user_profile = {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "xp": user["xp"] or 1250,
        "level": user["level"] or 4,
        "weight_kg": user["weight_kg"],
        "height_cm": user["height_cm"],
        "age": user["age"],
        "gender": user["gender"],
        "activity_level": user["activity_level"],
        "goal": user["goal"],
    }

    if user.get("settings"):
        user_profile["settings"] = json.loads(user["settings"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_profile,
    }
