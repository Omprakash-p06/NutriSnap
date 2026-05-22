import asyncio
import os
import sys
import json
from loguru import logger

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.routers.food import _search_local, _search_off, _search_gemini

async def test_search(query):
    print(f"Testing search for: '{query}'")
    
    # Tier 3 (Local)
    local = _search_local(query)
    print(f"Local DB: {local}")
    
    # Tier 1 (OFF)
    off = _search_off(query)
    print(f"OpenFoodFacts: {off}")
    
    # Tier 2 (Gemini)
    try:
        gemini = await _search_gemini(query)
        print(f"Gemini AI: {gemini}")
    except Exception as e:
        print(f"Gemini AI Exception: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "curd rice"
    
    # Load environment variables
    from dotenv import load_dotenv
    # Try loading from backend/.env if running from workspace root
    load_dotenv(os.path.join(os.getcwd(), "backend", ".env"))
    # Try loading from .env if running from backend folder
    load_dotenv()

    # Ensure API keys are set
    if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" not in os.environ:
        logger.warning("Neither GOOGLE_API_KEY nor GEMINI_API_KEY is set in environment!")
    
    asyncio.run(test_search(query))
