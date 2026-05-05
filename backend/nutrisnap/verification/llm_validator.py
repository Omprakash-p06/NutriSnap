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
from nutrisnap.verification.api_fallback import GeminiFallback

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
SYSTEM_PROMPT = """You are a nutrition validation system for a computer vision-based meal analyzer.
Your job is to verify meal predictions for realism and catch hallucinations.

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

Respond ONLY with valid JSON (no markdown, no explanation outside JSON):
{{
  "is_valid": <true/false>,
  "reasoning": "<brief explanation of issues found>",
  "corrections": [
    {{"original": "<item or value>", "corrected": "<new value or null>", "action": "<remove|correct|merge>"}},
    ...
  ]
}}

If everything is valid, return:
{{"is_valid": true, "reasoning": "All items plausible", "corrections": []}}"""


def _extract_json_from_text(text: str) -> dict | None:
    """Extract JSON from LLM response, handling markdown and noise."""
    # Try direct parse first
    text = text.strip()

    # Remove markdown code blocks
    if "```" in text:
        # Find the JSON block
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)
        else:
            # Try to find any JSON-like structure
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                text = match.group(0)

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
            logger.warning(f"JSON recovery failed: {e}")
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
        self.model_name = model_name or os.environ.get("LLM_MODEL", "gemini-2.0-flash")
        self.use_openrouter = self.provider == "openrouter"

        # Gemini fallback for API calls
        self._gemini = GeminiFallback(model_name=self.model_name, api_key=api_key)

        # API Keys
        self._openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        self._openai_key = os.environ.get("OPENAI_API_KEY")

        logger.info(
            f"LLMValidator initialized (provider: {self.provider}, model: {self.model_name})"
        )

    @property
    def is_available(self) -> bool:
        if self.provider == "openrouter":
            return self._openrouter_key is not None
        if self.provider == "openai":
            return self._openai_key is not None
        return self._gemini.is_available

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
        if self.provider == "openrouter":
            return await self._call_openrouter(prompt)
        elif self.provider == "openai":
            return await self._call_openai(prompt)
        elif self.provider == "gemini":
            return await self._call_gemini(prompt, image_path)
        else:
            # Fallback to Gemini if available, otherwise mock
            if self._gemini.is_available:
                return await self._call_gemini(prompt, image_path)
            
            return {
                "is_valid": True,
                "reasoning": "No API available, assuming valid",
                "corrections": [],
            }

    async def _call_gemini(self, prompt: str, image_path: str | None = None) -> dict:
        """Call Gemini API via existing fallback."""
        try:
            import google.generativeai as genai

            api_key = self._gemini._api_key or os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("No API key")

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.model_name)

            response = model.generate_content(prompt)
            text = response.text

            return self._parse_response(text)

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return {"is_valid": True, "reasoning": f"API error: {e}", "corrections": []}

    async def _call_openrouter(self, prompt: str) -> dict:
        """Call OpenRouter API."""
        import httpx

        endpoint = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._openrouter_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint, json=data, headers=headers, timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                text = result["choices"][0]["message"]["content"]
                return self._parse_response(text)

        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}")
            return {"is_valid": True, "reasoning": f"API error: {e}", "corrections": []}

    async def _call_openai(self, prompt: str) -> dict:
        """Call OpenAI API."""
        import httpx

        endpoint = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._openai_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"} if "gpt-4" in self.model_name else None
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint, json=data, headers=headers, timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                text = result["choices"][0]["message"]["content"]
                return self._parse_response(text)

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return {"is_valid": True, "reasoning": f"API error: {e}", "corrections": []}

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
            final_items=items_json,
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
