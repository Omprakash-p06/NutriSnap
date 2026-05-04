"""Authentication endpoints — signup and login."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import create_access_token, get_password_hash, verify_password
from app.database import get_database
from app.schemas import Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=UserOut, status_code=201)
async def signup(user_data: UserCreate):
    """Register a new user account."""
    db = await get_database()
    
    async with db.execute("SELECT * FROM users WHERE email = ?", (user_data.email,)) as cursor:
        if await cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

    query = """
        INSERT INTO users (email, full_name, hashed_password)
        VALUES (?, ?, ?)
    """
    params = (
        user_data.email,
        user_data.full_name,
        get_password_hash(user_data.password)
    )
    
    cursor = await db.execute(query, params)
    await db.commit()
    
    return {
        "_id": str(cursor.lastrowid),
        "email": user_data.email,
        "full_name": user_data.full_name,
        "created_at": datetime.now(timezone.utc)
    }


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate and return a JWT access token."""
    db = await get_database()
    
    async with db.execute("SELECT * FROM users WHERE email = ?", (form_data.username,)) as cursor:
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
    return {"access_token": token, "token_type": "bearer"}

