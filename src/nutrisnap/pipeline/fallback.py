"""LLM Fallback Predictor for NutriSnap.

Uses Gemini 1.5 Flash to provide a second opinion on flagged predictions.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import google.generativeai as genai
from PIL import Image

logger = logging.getLogger(__name__)


class GeminiFallback:
    """Multimodal fallback using Google's Gemini 1.5 Flash."""

    def __init__(self, config_path: str = "configs/api/config.yaml"):
        import yaml

        with open(config_path) as f:
            self.cfg = yaml.safe_load(f)["pipeline"]["fallback"]

        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.enabled = self.cfg.get("enabled", False) and self.api_key is not None

        if self.enabled:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                self.cfg.get("model", "gemini-1.5-flash")
            )

            with open(self.cfg["prompt_path"]) as f:
                self.prompt_template = f.read()
            logger.info(f"GeminiFallback initialized with model {self.cfg['model']}")
        else:
            logger.warning(
                "GeminiFallback disabled (disabled in config or missing GEMINI_API_KEY)"
            )

    async def refine(
        self, image_path: Path, initial_results: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """Request a second opinion from Gemini for a flagged image."""
        if not self.enabled:
            if os.environ.get("NUTRISNAP_MOCK_GEMINI") == "true":
                return self._mock_response(initial_results)
            return None

        try:
            # Prepare multimodal content
            img = Image.open(image_path)

            prompt = (
                self.prompt_template
                + f"\n\nINITIAL ESTIMATES:\n{json.dumps(initial_results, indent=2)}"
            )

            # Run in thread pool to avoid blocking asyncio
            response = await asyncio.to_thread(
                self.model.generate_content, [prompt, img]
            )

            if not response.text:
                logger.warning("Gemini returned empty response")
                return None

            # Parse JSON from response
            # Sometimes Gemini wraps JSON in ```json ... ```
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            refined = json.loads(text)
            logger.info(
                f"Gemini successfully refined estimate: {refined.get('reasoning')}"
            )
            return refined

        except Exception as e:
            logger.error(f"Gemini fallback failed: {str(e)}")
            return None

    def _mock_response(self, initial_results: Dict[str, float]) -> Dict[str, Any]:
        """Provide a simulated Gemini response for development/testing."""
        logger.info("MOCK MODE: Simulating Gemini response")
        # Just return slightly adjusted values
        return {
            "calories": initial_results.get("calories", 0) * 1.05,
            "fat": initial_results.get("fat", 0) * 1.02,
            "carbs": initial_results.get("carbs", 0) * 1.08,
            "protein": initial_results.get("protein", 0) * 1.0,
            "reasoning": "MOCK REFINEMENT: Slightly adjusted calories and carbs based on visual portion size.",
            "confidence": 0.85,
        }
