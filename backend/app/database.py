"""MongoDB async connection utilities."""

import os

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

_client: AsyncIOMotorClient | None = None
_db = None


async def connect_to_mongo():
    global _client, _db
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB", "nutrisnap")
    _client = AsyncIOMotorClient(mongo_uri)
    _db = _client[db_name]
    logger.info(f"Connected to MongoDB: {db_name}")


async def close_mongo_connection():
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")


async def get_database():
    return _db
