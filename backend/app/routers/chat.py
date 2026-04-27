"""AI Nutrition Assistant — real-time WebSocket chat powered by Gemini 2.0 Flash."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from loguru import logger

from app.auth import get_current_user_ws
from app.database import get_database

router = APIRouter(tags=["chat"])

# ─────────────────────────────────────────────────────────────────────────────
# Gemini persona
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are NutriSnap AI — a knowledgeable, warm, and empathetic nutrition coach.
Your mission is to help the user understand their meals, reach their health goals, and build sustainable habits.

Guidelines:
- Be concise (2-4 sentences unless the user asks for detail).
- Use the provided meal context to give personalised, specific advice.
- Never diagnose, treat, or replace a licensed dietitian.
- Celebrate progress. Never shame the user about food choices.
- Handle Indian, Asian, Mediterranean, and Western cuisines with equal expertise.
- If calorie or macro information is unavailable, give a reasonable estimate and say so.
"""


def _build_context_prompt(profile: dict, recent_logs: list[dict]) -> str:
    """Prepend user-specific context to the first user message."""
    tdee = profile.get("tdee_kcal", "unknown")
    goal = profile.get("goal", "maintain")
    logs_summary = ""
    for log in recent_logs[-5:]:  # last 5 meals
        name = log.get("food_name", "a meal")
        cal = log.get("calories", "?")
        logs_summary += f"  - {name}: {cal} kcal\n"
    if not logs_summary:
        logs_summary = "  No meals logged yet today.\n"
    return (
        f"[User context]\n"
        f"Daily calorie target (TDEE): {tdee} kcal\n"
        f"Goal: {goal}\n"
        f"Recent meals:\n{logs_summary}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket) -> None:
    """Real-time nutrition assistant chat.

    Protocol (JSON messages):
        Client → Server: {"type": "message", "content": "..."}
        Server → Client: {"type": "reply", "content": "...", "done": false}
        Server → Client: {"type": "reply", "content": "", "done": true}  # stream end
        Server → Client: {"type": "error", "content": "..."}
    """
    await websocket.accept()

    # Authenticate via query param token
    try:
        current_user = await get_current_user_ws(websocket)
    except Exception:
        await websocket.send_json({"type": "error", "content": "Unauthorized"})
        await websocket.close(code=1008)
        return

    # Load user profile + recent meal logs for context
    try:
        db = await get_database()
        user_id = str(current_user["_id"])
        profile_doc = await db.users.find_one({"_id": current_user["_id"]})
        profile = profile_doc or {}
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        cursor = db.meal_logs.find({"user_id": user_id, "timestamp": {"$gte": today_start}})
        recent_logs = await cursor.to_list(length=10)
    except Exception as exc:
        logger.warning(f"Could not load user context: {exc}")
        profile = {}
        recent_logs = []

    # Configure Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        await websocket.send_json({"type": "error", "content": "Gemini API key not configured."})
        await websocket.close()
        return

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=_SYSTEM_PROMPT,
        )
        chat_session = model.start_chat(history=[])
    except Exception as exc:
        logger.error(f"Gemini init failed: {exc}")
        await websocket.send_json({"type": "error", "content": "AI assistant unavailable."})
        await websocket.close()
        return

    context_injected = False
    logger.info(f"Chat session started for user {user_id}")

    try:
        while True:
            data = await websocket.receive_json()
            user_text: str = data.get("content", "").strip()
            if not user_text:
                continue

            # Inject user context once at the start of the session
            if not context_injected:
                context_preamble = _build_context_prompt(profile, recent_logs)
                user_text = f"{context_preamble}\n\nUser: {user_text}"
                context_injected = True

            # Stream response
            try:
                response = chat_session.send_message(user_text, stream=True)
                for chunk in response:
                    if chunk.text:
                        await websocket.send_json({
                            "type": "reply",
                            "content": chunk.text,
                            "done": False,
                        })
                await websocket.send_json({"type": "reply", "content": "", "done": True})
            except Exception as exc:
                logger.error(f"Gemini streaming error: {exc}")
                await websocket.send_json({"type": "error", "content": str(exc)})

    except WebSocketDisconnect:
        logger.info(f"Chat session ended for user {user_id}")
    except Exception as exc:
        logger.error(f"Unexpected chat error: {exc}")
        try:
            await websocket.send_json({"type": "error", "content": "Session error."})
        except Exception:
            pass
