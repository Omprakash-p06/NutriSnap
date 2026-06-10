"""SQLite async connection utilities."""

import aiosqlite
from loguru import logger

DB_PATH = "nutrisnap.db"
_db: aiosqlite.Connection | None = None


async def connect_to_database():
    """Initializes SQLite database and creates tables if they don't exist."""
    global _db
    _db = await aiosqlite.connect(DB_PATH)
    _db.row_factory = aiosqlite.Row

    # Initialize tables
    await _db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            full_name TEXT,
            hashed_password TEXT,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            settings TEXT, -- JSON string
            weight_kg REAL,
            height_cm REAL,
            age INTEGER,
            gender TEXT,
            activity_level TEXT,
            goal TEXT,
            location TEXT
        )
    """)

    # Dynamically alter table to add location column if users table was created earlier
    try:
        await _db.execute("ALTER TABLE users ADD COLUMN location TEXT")
    except Exception:
        pass

    await _db.execute("""
        CREATE TABLE IF NOT EXISTS meal_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            food_name TEXT,
            calories REAL,
            protein REAL,
            carbs REAL,
            fat REAL,
            mass_g REAL,
            category TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await _db.execute("""
        CREATE TABLE IF NOT EXISTS water_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            amount_ml INTEGER
        )
    """)

    await _db.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id TEXT PRIMARY KEY,
            user_email TEXT,
            status TEXT,
            result TEXT, -- JSON string
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await _db.execute("""
        CREATE TABLE IF NOT EXISTS social_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            user_name TEXT,
            meal_name TEXT,
            calories REAL,
            image_url TEXT,
            likes_count INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed guest user if absent
    async with _db.execute(
        "SELECT id FROM users WHERE email = 'guest@nutrisnap.ai'"
    ) as cur:
        if not await cur.fetchone():
            logger.info("Seeding guest user...")
            await _db.execute(
                """
                INSERT INTO users (email, full_name, hashed_password, xp, level, weight_kg, height_cm, age, gender, activity_level, goal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    "guest@nutrisnap.ai",
                    "Guest User",
                    "$2b$12$LQv3c1yqBWVHxkd0LpZ8aeX9Q0yXJ2J0yXJ2J0yXJ2J0yXJ2J0yXJ2",  # hashed 'nutrisnap'
                    1250,
                    4,
                    75.0,
                    180.0,
                    28,
                    "male",
                    "1.55",
                    "maintain",
                ),
            )

    await _db.commit()
    logger.info(f"SQLite database initialized at {DB_PATH}")


async def close_database_connection():
    if _db:
        await _db.close()
        logger.info("SQLite connection closed")


async def get_database():
    return _db


def is_mock_db():
    # With SQLite, we always have a persistent DB, so we don't need "mock" mode
    return False
