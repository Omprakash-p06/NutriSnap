"""Shared LLM gateway with provider fallback for NutriSnap.

This module centralizes Gemini, OpenRouter, and OpenAI access so the rest of
the codebase can treat the LLM as a fallback chain rather than a single hard-
coded provider.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import mimetypes
import os
import re
from pathlib import Path
from typing import Any

import httpx
from PIL import Image

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_PROVIDER_ORDER = ("local", "gemini", "openrouter", "openai")


def _first_env_value(*values: str | None, names: tuple[str, ...] = ()) -> str | None:
    for value in values:
        if value:
            return value
    for name in names:
        env_value = os.getenv(name)
        if env_value:
            return env_value
    return None


def _normalize_provider(provider: str | None) -> str:
    value = (provider or os.getenv("LLM_PROVIDER", "gemini")).strip().lower()
    return value if value in DEFAULT_PROVIDER_ORDER else "gemini"


def _default_model_for(provider: str) -> str:
    if provider == "local":
        return _first_env_value(
            names=("LOCAL_LLM_MODEL",),
        ) or os.getenv("LLM_MODEL", "gemma4:2b")

    if provider == "openrouter":
        return _first_env_value(
            names=("OPENROUTER_MODEL",),
        ) or os.getenv("LLM_MODEL", "google/gemma-4-26b-a4b-it:free")

    if provider == "openai":
        return _first_env_value(
            names=("OPENAI_MODEL",),
        ) or os.getenv("LLM_MODEL", "gpt-4o-mini")

    return _first_env_value(names=("GEMINI_MODEL",)) or os.getenv(
        "LLM_MODEL", "gemini-2.5-flash"
    )


def _provider_order(preferred: str) -> list[str]:
    order = [preferred] if preferred in DEFAULT_PROVIDER_ORDER else ["gemini"]
    for provider in DEFAULT_PROVIDER_ORDER:
        if provider not in order:
            order.append(provider)
    return order


def _extract_json_from_text(text: str) -> Any:
    text = text.strip()

    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\[{].*?[\]}])\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)

    match = re.search(r"([\[{].*[\]}])", text, re.DOTALL)
    if match:
        text = match.group(1)

    text = text.strip().strip("`").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        text = re.sub(r",\s*\}", "}", text)
        text = re.sub(r",\s*\]", "]", text)
        text = re.sub(r"(\w+):", r'"\1":', text)
        return json.loads(text)


def _image_to_bytes_and_mime(image_input: Any) -> tuple[bytes, str] | None:
    if image_input is None:
        return None

    if isinstance(image_input, (bytes, bytearray)):
        return bytes(image_input), "image/jpeg"

    if isinstance(image_input, Image.Image):
        buffer = io.BytesIO()
        image_input.save(buffer, format="JPEG")
        return buffer.getvalue(), "image/jpeg"

    if isinstance(image_input, (str, Path)):
        path = Path(image_input)
        if not path.exists():
            return None
        mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        return path.read_bytes(), mime_type

    return None


def _build_openai_content(prompt: str, image_input: Any | None) -> Any:
    image_payload = _image_to_bytes_and_mime(image_input)
    if not image_payload:
        return prompt

    image_bytes, mime_type = image_payload
    data_url = base64.b64encode(image_bytes).decode("ascii")
    return [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{data_url}"}},
    ]


class LLMService:
    """Provider-aware LLM gateway with automatic fallback."""

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        provider: str | None = None,
    ) -> None:
        self.provider = _normalize_provider(provider)
        self.provider_order = _provider_order(self.provider)
        self.model_name = model_name or _default_model_for(self.provider)

        self._gemini_key = _first_env_value(
            api_key,
            names=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        )
        self._openrouter_key = _first_env_value(
            names=("OPENROUTER_API_KEY", "OPENROUTER_API_KEY_FALLBACK", "OPENROUTER_KEY"),
        )
        self._openai_key = _first_env_value(names=("OPENAI_API_KEY",))

        self._last_provider: str | None = None
        self._last_error: Exception | None = None

    @property
    def is_available(self) -> bool:
        return any(
            (
                True,  # local provider is always "potentially" available
                self._gemini_key,
                self._openrouter_key,
                self._openai_key,
            )
        )

    @property
    def last_provider(self) -> str | None:
        return self._last_provider

    @property
    def last_error(self) -> Exception | None:
        return self._last_error

    def _provider_ready(self, provider: str) -> bool:
        if provider == "local":
            # Always attempt — connection errors trigger graceful fallback
            return True
        if provider == "gemini":
            return self._gemini_key is not None
        if provider == "openrouter":
            return self._openrouter_key is not None
        if provider == "openai":
            return self._openai_key is not None
        return False

    def _model_for_provider(self, provider: str) -> str:
        if provider == "local":
            return _default_model_for("local")
        if provider == "gemini":
            return _default_model_for("gemini")
        if provider == "openrouter":
            return _default_model_for("openrouter")
        if provider == "openai":
            return _default_model_for("openai")
        return self.model_name

    def _is_transient_failure(self, exc: Exception) -> bool:
        message = str(exc).lower()
        transient_markers = (
            "429",
            "rate limit",
            "quota",
            "temporarily unavailable",
            "unavailable",
            "deprecated",
            "not found",
            "404",
            "503",
            "service unavailable",
            "aborted",
        )
        return any(marker in message for marker in transient_markers)

    async def _call_local(self, prompt: str, image_input: Any | None = None) -> str:
        """Call a local OpenAI-compatible endpoint (Ollama, llama.cpp server, LM Studio).

        Image inputs are silently ignored — Gemma 4 2B/4B text-only by default.
        For multimodal local inference, upgrade to llava or a vision-capable model.
        """
        base_url = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1")
        endpoint = f"{base_url.rstrip('/')}/chat/completions"
        timeout = float(os.getenv("LOCAL_LLM_TIMEOUT", "90"))

        payload = {
            "model": self._model_for_provider("local"),
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint, json=payload, timeout=timeout,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()

            if "error" in data:
                error_msg = data["error"].get("message", str(data["error"]))
                raise ValueError(f"Local LLM error: {error_msg}")

            if "choices" not in data or not data["choices"]:
                raise ValueError(f"Local LLM response missing 'choices': {data}")

            return data["choices"][0]["message"]["content"] or ""

        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Local LLM not reachable at {base_url}. "
                "Is Ollama running? Try: ollama serve"
            ) from exc

    async def _call_gemini(self, prompt: str, image_input: Any | None = None) -> str:
        def _sync_call() -> str:
            import google.generativeai as genai

            genai.configure(api_key=self._gemini_key)
            model = genai.GenerativeModel(self._model_for_provider("gemini"))

            content: list[Any] = [prompt]
            image_payload = _image_to_bytes_and_mime(image_input)
            if image_payload:
                image_bytes, _ = image_payload
                content.append(Image.open(io.BytesIO(image_bytes)))

            response = model.generate_content(content)
            return getattr(response, "text", "") or ""

        return await asyncio.to_thread(_sync_call)

    async def _call_openrouter(self, prompt: str, image_input: Any | None = None) -> str:
        endpoint = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._openrouter_key}",
            "Content-Type": "application/json",
        }
        referer = os.getenv("OPENROUTER_HTTP_REFERER")
        title = os.getenv("OPENROUTER_TITLE")
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-OpenRouter-Title"] = title

        payload = {
            "model": self._model_for_provider("openrouter"),
            "messages": [
                {
                    "role": "user",
                    "content": _build_openai_content(prompt, image_input),
                }
            ],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload, headers=headers, timeout=45.0)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error_msg = data["error"].get("message", str(data["error"]))
                raise ValueError(f"OpenRouter API error: {error_msg}")

            if "choices" not in data or not data["choices"]:
                raise ValueError(f"OpenRouter response missing 'choices': {data}")

            return data["choices"][0]["message"]["content"] or ""

    async def _call_openai(self, prompt: str, image_input: Any | None = None) -> str:
        endpoint = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._openai_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model_for_provider("openai"),
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": _build_openai_content(prompt, image_input)},
            ],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload, headers=headers, timeout=45.0)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error_msg = data["error"].get("message", str(data["error"]))
                raise ValueError(f"OpenAI API error: {error_msg}")

            if "choices" not in data or not data["choices"]:
                raise ValueError(f"OpenAI response missing 'choices': {data}")

            return data["choices"][0]["message"]["content"] or ""

    async def generate_text(self, prompt: str, image_input: Any | None = None) -> str:
        """Generate raw text with provider fallback."""
        last_error: Exception | None = None

        for provider in self.provider_order:
            if not self._provider_ready(provider):
                continue

            try:
                if provider == "local":
                    text = await self._call_local(prompt, image_input)
                elif provider == "gemini":
                    text = await self._call_gemini(prompt, image_input)
                elif provider == "openrouter":
                    text = await self._call_openrouter(prompt, image_input)
                else:
                    text = await self._call_openai(prompt, image_input)

                if not text.strip():
                    raise ValueError(f"{provider} returned an empty response")

                self._last_provider = provider
                self._last_error = None
                return text
            except Exception as exc:
                last_error = exc
                self._last_error = exc
                logger.warning(f"LLM provider {provider} failed: {exc}")
                if provider == self.provider and not self._is_transient_failure(exc):
                    # Keep trying fallbacks even for non-transient failures, but log the first cause.
                    pass

        if last_error:
            raise last_error
        raise RuntimeError("No LLM provider is configured")

    async def generate_json(self, prompt: str, image_input: Any | None = None) -> Any:
        """Generate and parse JSON with provider fallback."""
        text = await self.generate_text(prompt, image_input)
        parsed = _extract_json_from_text(text)
        if parsed is None:
            raise ValueError("LLM returned non-JSON content")
        return parsed
