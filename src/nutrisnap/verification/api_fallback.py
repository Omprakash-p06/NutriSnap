"""Gemini 2.0 Flash API fallback for NutriSnap nutrition verification.

Implements Tier 2 (2-step prompt) and hooks for Tier 3 (USDA).
"""
import json
import os
from dataclasses import dataclass
from typing import Any, Optional

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

# Uncertainty trigger thresholds
ENSEMBLE_STD_THRESHOLD = 50.0  # kcal
CONFIDENCE_THRESHOLD = 0.7


@dataclass
class FallbackResult:
    calories: float
    protein: float
    carbs: float
    fat: float
    source: str  # "cv_model" | "gemini_api" | "gemini_error"
    explanation: Optional[str] = None
    identified_items: Optional[list[str]] = None
    raw_response: Optional[str] = None


# Strategic 2-Step Prompts (P142-145)

PROMPT_STEP1 = """Analyze this meal photo.
1. Identify all food items visible.
2. Estimate the calories, protein, carbs, and fat for the QUANTITY shown.

Respond with a list of items and their estimated macros.
"""

PROMPT_STEP2 = """A computer vision model predicted these values for the same image:
- Calories: {cv_cal:.1f} kcal
- Protein: {cv_prot:.1f} g
- Carbs: {cv_carb:.1f} g
- Fat: {cv_fat:.1f} g

Based on your own identification ({gemini_items}), are the computer vision values realistic?
If they are significantly off, provides corrected values.

Respond ONLY with valid JSON (no markdown):
{{
  "calories": <number>,
  "protein": <number>,
  "carbs": <number>,
  "fat": <number>,
  "identified_items": ["item1", "item2", ...],
  "reasoning": "<brief explanation>"
}}"""


class GeminiFallback:
    """Gemini 2.0 Flash API (Tier 2) verification."""

    def __init__(
        self, model_name: str = "gemini-2.0-flash", api_key: str | None = None
    ):
        self.model_name = model_name
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self._model = None

        if self._api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self._api_key)
                self._model = genai.GenerativeModel(model_name)
                logger.info(f"Gemini 2.0 Flash fallback ready ({model_name})")
            except ImportError:
                logger.warning("google-generativeai not installed.")
        else:
            logger.warning("GEMINI_API_KEY missing.")

    @property
    def is_available(self) -> bool:
        return self._model is not None

    def verify(self, image: Any, cv_prediction: dict) -> FallbackResult:
        """Execute 2-step verification strategy (P142)."""
        cv_cal = float(cv_prediction.get("calories", 0))
        cv_prot = float(cv_prediction.get("protein", 0))
        cv_carb = float(cv_prediction.get("carbs", 0))
        cv_fat = float(cv_prediction.get("fat", 0))

        if not self.is_available:
            return FallbackResult(cv_cal, cv_prot, cv_carb, cv_fat, "cv_model")

        try:
            # Step 1: Independent identification
            chat = self._model.start_chat()
            res1 = chat.send_message([PROMPT_STEP1, image])
            step1_text = res1.text

            # Step 2: Comparison & Correction
            p2 = PROMPT_STEP2.format(
                cv_cal=cv_cal,
                cv_prot=cv_prot,
                cv_carb=cv_carb,
                cv_fat=cv_fat,
                gemini_items=step1_text,
            )
            res2 = chat.send_message(p2)
            raw_json = res2.text.strip()

            if "```" in raw_json:
                raw_json = raw_json.split("```json")[-1].split("```")[0].strip()

            data = json.loads(raw_json)

            return FallbackResult(
                calories=float(data.get("calories", cv_cal)),
                protein=float(data.get("protein", cv_prot)),
                carbs=float(data.get("carbs", cv_carb)),
                fat=float(data.get("fat", cv_fat)),
                source="gemini_api",
                explanation=data.get("reasoning"),
                identified_items=data.get("identified_items"),
                raw_response=raw_json,
            )

        except Exception as e:
            logger.error(f"Gemini fallback failed: {e}")
            return FallbackResult(
                cv_cal, cv_prot, cv_carb, cv_fat, "gemini_error", explanation=str(e)
            )
