"""AI Nutrition Assistant via WebSocket — powered by Gemini 2.0 Flash."""
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter(prefix="/chat", tags=["chat"])

_SYSTEM_PROMPT = (
    "You are a knowledgeable, friendly AI nutritionist called NutriBot. "
    "Answer questions about food, nutrition, calories, macros, meal planning, and health goals "
    "concisely and accurately. Be supportive and science-based. "
    "If the user shares what they ate, estimate the calories and give brief advice."
)


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket):
    """WebSocket chat endpoint that streams AI nutritionist responses."""
    await websocket.accept()
    logger.info("Chat WebSocket connected")

    try:
        import google.generativeai as genai

        genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
        model = genai.GenerativeModel("gemini-2.0-flash")
        chat = model.start_chat()

        while True:
            message = await websocket.receive_text()
            response = chat.send_message(f"{_SYSTEM_PROMPT}\n\nUser: {message}")
            await websocket.send_text(response.text)

    except WebSocketDisconnect:
        logger.info("Chat WebSocket disconnected cleanly")
    except Exception as exc:
        logger.error(f"Chat WebSocket error: {exc}")
        try:
            await websocket.send_text(f"Error: {exc}")
        except Exception:
            pass
