"""LLM fallback for NutriSnap nutrition verification."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

from nutrisnap.utils.logger import get_logger
from nutrisnap.verification.llm_service import LLMService

logger = get_logger(__name__)


@dataclass
class FallbackResult:
    calories: float
    protein: float
    carbs: float
    fat: float
    source: str
    explanation: Optional[str] = None
    identified_items: Optional[list[str]] = None
    raw_response: Optional[str] = None


class GeminiFallback:
    """Provider-fallback verification for nutrition predictions."""

    def __init__(
        self, model_name: str = "gemini-2.5-flash", api_key: str | None = None
    ):
        self.model_name = model_name
        self._service = LLMService(
            model_name=model_name,
            api_key=api_key,
            provider=os.environ.get("LLM_PROVIDER", "gemini"),
        )

        if self._service.is_available:
            logger.info(
                f"LLM fallback ready ({self._service.provider} -> {self._service.model_name})"
            )
        else:
            logger.warning("No Gemini/OpenRouter/OpenAI key configured.")

    @property
    def is_available(self) -> bool:
        return self._service.is_available

    async def verify(self, image: Any, cv_prediction: dict) -> FallbackResult:
        """Compare a pipeline prediction against an AI review and return the final answer."""
        cv_cal = float(cv_prediction.get("calories", 0))
        cv_prot = float(cv_prediction.get("protein", 0))
        cv_carb = float(cv_prediction.get("carbs", 0))
        cv_fat = float(cv_prediction.get("fat", 0))

        if os.environ.get("NUTRISNAP_MOCK_GEMINI") == "true":
            return FallbackResult(
                calories=100.0,
                protein=10.0,
                carbs=10.0,
                fat=2.0,
                source="gemini_api",
                explanation="MOCK REFINEMENT",
                identified_items=["mock_food"],
                raw_response='{"confidence": 0.85}',
            )

        if not self.is_available:
            return FallbackResult(cv_cal, cv_prot, cv_carb, cv_fat, "cv_model")

        prompt = f"""Analyze this meal photo and compare it to the computer-vision pipeline output.

Pipeline prediction:
- Calories: {cv_cal:.1f} kcal
- Protein: {cv_prot:.1f} g
- Carbs: {cv_carb:.1f} g
- Fat: {cv_fat:.1f} g

First, independently identify the food items in the image.
Then compare your own interpretation with the pipeline values and correct them if needed.

Respond ONLY with valid JSON:
{{
  "calories": <number>,
  "protein": <number>,
  "carbs": <number>,
  "fat": <number>,
  "identified_items": ["item1", "item2", ...],
  "reasoning": "<brief explanation>"
}}"""

        try:
            data = await self._service.generate_json(prompt, image)
            if not isinstance(data, dict):
                raise ValueError("Unexpected fallback response format")

            return FallbackResult(
                calories=float(data.get("calories", cv_cal)),
                protein=float(data.get("protein", cv_prot)),
                carbs=float(data.get("carbs", cv_carb)),
                fat=float(data.get("fat", cv_fat)),
                source=self._service.last_provider or "gemini_api",
                explanation=data.get("reasoning"),
                identified_items=data.get("identified_items"),
                raw_response=json.dumps(data),
            )
        except Exception as exc:
            logger.error(f"LLM fallback failed: {exc}")
            return FallbackResult(
                cv_cal,
                cv_prot,
                cv_carb,
                cv_fat,
                "gemini_error",
                explanation=str(exc),
            )
