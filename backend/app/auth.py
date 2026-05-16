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

import bcrypt

# Password hashing logic using direct bcrypt to avoid passlib issues on Python 3.12+
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Verify JWT and return the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # If no token and it's optional, we could return Guest, 
    # but the user wants "accuracy", so we should enforce it for protected routes.
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db = await get_database()
    async with db.execute("SELECT * FROM users WHERE email = ?", (email,)) as cursor:
        row = await cursor.fetchone()
        if row is None:
            raise credentials_exception
        
        user = dict(row)
        if user.get("settings"):
            user["settings"] = json.loads(user["settings"])
        return user


async def get_current_user_ws(websocket) -> dict:
    """WebSocket auth using token from query param or header."""
    # For simplicity in WS, we can extract from query or use a default if missing
    # But let's try to be accurate
    token = websocket.query_params.get("token")
    if not token:
        return await get_current_user(None) # Will raise 401
    return await get_current_user(token)


