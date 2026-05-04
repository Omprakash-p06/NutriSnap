"""SQLite async connection utilities."""

import os
import sqlite3
import json
import aiosqlite
from loguru import logger

DB_PATH = "nutrisnap.db"
_db: aiosqlite.Connection | None = None


async def connect_to_mongo():
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
            goal TEXT
        )
    """)
    
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

    
    await _db.commit()
    logger.info(f"SQLite database initialized at {DB_PATH}")


async def close_mongo_connection():
    global _db
    if _db:
        await _db.close()
        logger.info("SQLite connection closed")


async def get_database():
    return _db


def is_mock_db():
    # With SQLite, we always have a persistent DB, so we don't need "mock" mode
    return False


