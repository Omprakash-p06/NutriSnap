"""JWT authentication utilities."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.database import get_database

SECRET_KEY = os.getenv("SECRET_KEY", "change_me_in_production_secret_key_32chars_")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Return a default guest user for the simplified MVP.
    
    JWT verification is bypassed to allow immediate access without login.
    """
    db = await get_database()
    guest_email = "guest@nutrisnap.ai"
    user = await db.users.find_one({"email": guest_email})
    
    if user is None:
        user = {
            "email": guest_email,
            "full_name": "Guest User",
            "hashed_password": "no_password_needed",
            "xp": 0,
            "level": 1,
            "settings": {
                "dailyCalorieGoal": 2000,
                "proteinGoal": 150,
                "carbsGoal": 200,
                "fatGoal": 70
            }
        }
        result = await db.users.insert_one(user)
        user["_id"] = result.inserted_id
    
    return user


async def get_current_user_ws(websocket) -> dict:
    """WebSocket auth bypass for the simplified MVP.
    
    Always returns the default guest user.
    """
    db = await get_database()
    guest_email = "guest@nutrisnap.ai"
    user = await db.users.find_one({"email": guest_email})
    
    if user is None:
        user = {
            "email": guest_email,
            "full_name": "Guest User",
            "hashed_password": "no_password_needed",
            "xp": 0,
            "level": 1,
            "settings": {}
        }
        result = await db.users.insert_one(user)
        user["_id"] = result.inserted_id
    
    return user
