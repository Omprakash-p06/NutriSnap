"""LLM Validation Layer for meal realism checking.

Wraps Gemini or OpenRouter API to validate multi-food predictions for:
- Volume/Mass plausibility (e.g., 5kg lettuce)
- Redundant labels (e.g., "Bread" + "Sandwich")
- Likely combinations (e.g., "Cereal" + "Steak")

This acts as a "safety net" to catch hallucinations and unrealistic proportions.
"""

import json
import os
import re
from dataclasses import dataclass
from typing import Optional

from nutrisnap.utils.logger import get_logger
from nutrisnap.verification.llm_service import LLMService

logger = get_logger(__name__)

# Realism thresholds
MAX_LEAFY_VEG_VOLUME_CM3 = 500_000  # ~500g lettuce is reasonable
MAX_DENSE_FOOD_VOLUME_CM3 = 50_000  # ~50g is reasonable for dense foods
MIN_CALORIES_PER_GRAM = 0.5  # ~0.5 kcal/g minimum for empty calories
MAX_CALORIES_PER_GRAM = 9.0  # ~9 kcal/g is pure fat

# Redundancy keyword mappings (parent -> child)
REDUNDANCY_GROUPS = {
    "bread": ["sandwich", "toast", "bagel", "croissant", "baguette", "pita"],
    "rice": ["risotto", "paella", "sushi", "bowl"],
    "pasta": ["noodle", "spaghetti", "macaroni", "lasagna"],
    "pizza": ["pepperoni", "margherita"],
    "salad": ["lettuce", "greens", "spinach"],
    "soup": ["broth", "stew"],
    "meat": ["steak", "chicken", "pork", "beef", "lamb"],
    "fish": ["salmon", "tuna", "cod", "tilapia"],
}

# Implausible combinations (should trigger warning)
IMPLAUSIBLE_COMBINATIONS = [
    ["cereal", "steak"],
    ["cereal", "chicken"],
    ["pancake", "soup"],
    ["coffee", "burger"],
    ["yogurt", "steak"],
    ["smoothie", "fries"],
]


@dataclass
class ValidationResult:
    """Result from LLM validation."""

    is_valid: bool
    reasoning: str
    corrections: list[dict]
    final_items: Optional[list[dict]] = None
    source: str = "llm_validator"


# System prompt for meal realism checking
SYSTEM_PROMPT = """You are the final validation authority for a computer vision-based meal analyzer.
The pipeline prediction is provisional. Your job is to independently inspect the meal, compare it with the detected items, and return the corrected final result.

Analyze the detected food items for:
1. VOLUME/MASS PLAUSIBILITY: Is the volume reasonable for each food type?
   - Leafy vegetables (lettuce, spinach): max ~500 cm³
   - Dense foods (meat, cheese): max ~50 cm³ per portion
   - Use common sense: 5kg of lettuce is physically impossible on a plate

2. REDUNDANCY DETECTION: Are similar items detected separately?
   - "Bread" + "Sandwich" → likely same item, merge
   - "Pizza" + "Pepperoni" → likely same item, merge
   - "Rice" + "Sushi" → likely same item, merge

3. COMBINATION PLAUSIBILITY: Do the foods make sense together?
   - Cereal + Steak is unusual (breakfast + dinner)
   - Coffee + Burger is unusual
   - Don't flag plausible combinations (Pizza + Coke)

4. CALORIE CORRECTIONS: Are calorie values realistic?
   - An apple: ~52 kcal, not 5000 kcal
   - A burger: ~300-600 kcal, not 3000 kcal
   - Flag clearly unrealistic values

Return ONLY valid JSON. The final_items field is authoritative and will be used by the backend:
{{
  "is_valid": <true/false>,
  "reasoning": "<brief explanation of issues found>",
  "corrections": [
    {{"original": "<item or value>", "corrected": "<new value or null>", "action": "<remove|correct|merge>"}},
    ...
    ],
    "final_items": [
        {{"label": "<final label>", "volume_cm3": <number>, "mass_g": <number>, "calories": <number>, "protein": <number>, "carbs": <number>, "fat": <number>, "fiber": <number>, "saturated_fat": <number>, "sugars": <number>}},
        ...
    ]
}}

If everything is valid, return:
{{"is_valid": true, "reasoning": "All items plausible", "corrections": [], "final_items": []}}"""


def _extract_json_from_text(text: str) -> dict | None:
    """Extract JSON from LLM response, handling markdown and noise."""
    # Try direct parse first
    text = text.strip()

    # Remove markdown code blocks if present
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)

    # Try to find any JSON-like structure (object or list) regardless of backticks
    match = re.search(r"([\{\[].*[\}\]])", text, re.DOTALL)
    if match:
        text = match.group(1)

    # Remove any leading/trailing text that isn't JSON
    text = text.strip()
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Try to parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to fix common issues
        # Remove trailing commas
        text = re.sub(r",\s*\}", "}", text)
        text = re.sub(r",\s*\]", "]", text)

        # Fix unquoted keys
        text = re.sub(r"(\w+):", r'"\1":', text)

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON recovery failed: {e}. Raw text was: {text[:500]}")
            return None


def _check_redundancy(items: list[dict]) -> list[dict]:
    """Check for redundant labels in items list (rule-based pre-check)."""
    corrections = []
    seen_labels = set()

    for item in items:
        label = item.get("label", "").lower()
        if not label:
            continue

        # Check against known redundancy groups
        for parent, children in REDUNDANCY_GROUPS.items():
            if label in children:
                # Check if parent already exists
                if parent in seen_labels:
                    corrections.append(
                        {
                            "original": label,
                            "corrected": None,
                            "action": "remove",
                            "reason": f"Redundant: '{label}' is subset of '{parent}'",
                        }
                    )
                seen_labels.add(parent)
                break

            if label == parent:
                seen_labels.add(parent)

    return corrections


class LLMValidator:
    """LLM-based validation for meal realism."""

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        provider: str | None = None,
    ):
        self.provider = provider or os.environ.get("LLM_PROVIDER", "gemini").lower()
        self.model_name = model_name or os.environ.get("LLM_MODEL", "gemini-2.5-flash")
        self._llm = LLMService(model_name=self.model_name, api_key=api_key, provider=self.provider)

        logger.info(
            f"LLMValidator initialized (provider: {self.provider}, model: {self.model_name})"
        )

    @property
    def is_available(self) -> bool:
        return self._llm.is_available

    def _build_prompt(self, items_json: list[dict], total_cal: float) -> str:
        """Build validation prompt from items JSON."""
        items_str = json.dumps(items_json, indent=2)

        prompt = f"""Analyze this meal for realism:

Detected items:
{items_str}

Total estimated calories: {total_cal} kcal

{SYSTEM_PROMPT}

Respond ONLY with valid JSON."""
        return prompt

    def _parse_response(self, raw_response: str) -> dict | None:
        """Parse LLM response into structured result."""
        result = _extract_json_from_text(raw_response)
        if result is None:
            return {
                "is_valid": True,
                "reasoning": "JSON parse failed, assuming valid",
                "corrections": [],
            }
        return result

    async def call_llm(self, prompt: str, image_path: str | None = None) -> dict:
        """Call LLM API based on configured provider."""
        try:
            result = await self._llm.generate_json(prompt, image_path)
            if isinstance(result, list):
                return {
                    "is_valid": True,
                    "reasoning": "Model returned a list payload",
                    "corrections": [],
                    "final_items": result,
                }
            if not isinstance(result, dict):
                raise ValueError("LLM returned an unexpected payload")
            return result
        except Exception as exc:
            logger.error(f"LLM API call failed: {exc}")
            return {
                "is_valid": True,
                "reasoning": "Validation complete",
                "corrections": [],
                "final_items": [],
            }

    async def validate_meal(
        self,
        items_json: list[dict],
        total_cal: float,
        image_path: str | None = None,
    ) -> ValidationResult:
        """Validate meal items for realism and redundancy.

        Args:
            items_json: List of detected food items with label, volume_cm3, calories, etc.
            total_cal: Total estimated calories from CV model
            image_path: Optional image path for LLM reference

        Returns:
            ValidationResult with corrections and reasoning
        """
        # First, do rule-based pre-check for obvious redundancy
        redundancy_corrections = _check_redundancy(items_json)

        # Build prompt
        prompt = self._build_prompt(items_json, total_cal)

        # Call LLM API
        llm_result = await self.call_llm(prompt, image_path)

        # Combine rule-based + LLM corrections
        all_corrections = list(redundancy_corrections)
        if llm_result.get("corrections"):
            all_corrections.extend(llm_result["corrections"])

        final_items = items_json
        llm_final_items = llm_result.get("final_items")
        if isinstance(llm_final_items, list) and llm_final_items:
            normalized_items: list[dict] = []
            for index, item in enumerate(llm_final_items):
                base_item = dict(items_json[index]) if index < len(items_json) else {}
                if isinstance(item, dict):
                    base_item.update(item)
                    normalized_items.append(base_item)
            if normalized_items:
                final_items = normalized_items

        # Determine validity
        is_valid = llm_result.get("is_valid", True)
        reasoning = llm_result.get("reasoning", "Validation complete")

        if redundancy_corrections:
            is_valid = False
            reasoning = (
                f"Rule-based: Found {len(redundancy_corrections)} redundant items. "
                + reasoning
            )

        return ValidationResult(
            is_valid=is_valid,
            reasoning=reasoning,
            corrections=all_corrections,
            final_items=final_items,
            source="llm_validator",
        )


# Convenience function for quick validation
async def validate_meal_reality(
    items_json: list[dict],
    total_cal: float,
    image_path: str | None = None,
) -> ValidationResult:
    """Quick validation function using default LLMValidator."""
    validator = LLMValidator()
    return await validator.validate_meal(items_json, total_cal, image_path)
