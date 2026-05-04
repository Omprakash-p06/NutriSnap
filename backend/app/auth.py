"""JWT authentication utilities."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

import json
from app.database import get_database, is_mock_db

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
    guest_email = "guest@nutrisnap.ai"
    db = await get_database()
    
    if db is None:
        return {
            "email": guest_email,
            "full_name": "Guest User (No DB)",
            "xp": 0,
            "level": 1,
            "settings": {}
        }

    default_settings = json.dumps({
        "dailyCalorieGoal": 2000,
        "proteinGoal": 150,
        "carbsGoal": 200,
        "fatGoal": 70
    })

    # Atomic upsert — INSERT OR IGNORE ensures we never hit a UNIQUE constraint
    # even when multiple concurrent requests arrive simultaneously.
    await db.execute(
        "INSERT OR IGNORE INTO users (email, full_name, hashed_password, settings) VALUES (?, ?, ?, ?)",
        (guest_email, "Guest User", "no_password_needed", default_settings)
    )
    await db.commit()
    
    async with db.execute("SELECT * FROM users WHERE email = ?", (guest_email,)) as cursor:
        row = await cursor.fetchone()
        user = dict(row)
        if user.get("settings"):
            user["settings"] = json.loads(user["settings"])
        return user



async def get_current_user_ws(websocket) -> dict:
    """WebSocket auth bypass for the simplified MVP."""
    return await get_current_user()


