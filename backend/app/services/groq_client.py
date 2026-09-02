"""Groq API client wrapper with model tiering, fallback, exponential backoff, and failure handling.
Features:
- Fast Tier (llama-3.1-8b-instant): Ultra-low latency (<150ms) for extraction, classification, and slot filling.
- Reasoning Tier (llama-3.3-70b-versatile / primary): High intelligence for multi-agent ReAct and synthesis.
"""

import asyncio
import logging
from typing import Any
from groq import AsyncGroq, APIError, APITimeoutError, RateLimitError
from app.config import settings

logger = logging.getLogger(__name__)


class GroqClient:
    """Async Groq client with model tiering, fallback, and automatic retry support."""

    def __init__(self):
        self._client = AsyncGroq(api_key=settings.groq_api_key)
        self.fast_model = settings.groq_model or "qwen/qwen3.8-27b"
        self.primary_model = settings.groq_model or "qwen/qwen3.8-27b"
        self.fallback_model = settings.groq_fallback_model or "openai/gpt-oss-120b"

    async def fast_completion(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.1,
        max_tokens: int = 256,
        response_format: dict[str, str] | None = None,
        max_retries: int = 2,
    ) -> Any:
        """Execute fast, low-latency extraction (<150ms) using lightweight LLaMA 3.1 8B Instant."""
        kwargs: dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        last_error = None
        for attempt in range(max_retries):
            try:
                response = await self._client.chat.completions.create(
                    model=self.fast_model,
                    **kwargs,
                )
                return response
            except (RateLimitError, APITimeoutError, APIError) as exc:
                last_error = exc
                logger.warning("Fast model %s attempt %d/%d failed: %s", self.fast_model, attempt + 1, max_retries, exc)
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.3 * (2 ** attempt))

        # Fallback to primary if fast fails
        try:
            return await self._client.chat.completions.create(
                model=self.primary_model,
                **kwargs,
            )
        except Exception:
            raise last_error

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] = "auto",
        temperature: float = 0.4,
        max_tokens: int = 1024,
        max_retries: int = 2,
    ) -> Any:
        """Execute chat completion with reasoning tier and automatic fallback on rate limit or timeout."""
        kwargs: dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        last_error = None
        # 1. Primary Model Attempt with retry
        for attempt in range(max_retries):
            try:
                response = await self._client.chat.completions.create(
                    model=self.primary_model,
                    **kwargs,
                )
                return response
            except (RateLimitError, APITimeoutError, APIError) as exc:
                last_error = exc
                logger.warning(
                    "Primary model %s attempt %d/%d failed with %s",
                    self.primary_model,
                    attempt + 1,
                    max_retries,
                    exc,
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5 * (2 ** attempt))

        # 2. Fallback Model Attempt with retry
        logger.warning(
            "Primary model exhausted. Initiating fallback to secondary model: %s",
            self.fallback_model,
        )
        for attempt in range(max_retries):
            try:
                response = await self._client.chat.completions.create(
                    model=self.fallback_model,
                    **kwargs,
                )
                logger.info("Successfully recovered using fallback model %s", self.fallback_model)
                return response
            except Exception as fallback_exc:
                last_error = fallback_exc
                logger.warning(
                    "Fallback model %s attempt %d/%d failed with %s",
                    self.fallback_model,
                    attempt + 1,
                    max_retries,
                    fallback_exc,
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5 * (2 ** attempt))

        logger.error("Both primary and fallback models failed completely: %s", last_error)
        raise last_error


groq_client = GroqClient()
