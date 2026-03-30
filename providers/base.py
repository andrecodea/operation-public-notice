"""Creates ABC for LLM provider with completion function"""

import asyncio
import logging
from abc import ABC, abstractmethod

import anthropic
import openai

from config.settings import LLMConfig

logger = logging.getLogger(__name__)

_RETRY_WAITS = [30, 60, 120]  # seconds between retries on rate limit


class LLMProvider(ABC):
    """Initializes ABC for providers with a chat completion abstract method."""
    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    async def complete(self, messages: list[dict]) -> str: ...


async def _with_retry(coro_fn, provider_name: str):
    """Runs coro_fn() with exponential backoff on RateLimitError. Raises on exhaustion."""
    for attempt, wait in enumerate(_RETRY_WAITS + [None]):
        try:
            return await coro_fn()
        except (openai.RateLimitError, anthropic.RateLimitError) as e:
            if wait is None:
                raise
            logger.warning(
                f"{provider_name} rate limited (attempt {attempt + 1}/{len(_RETRY_WAITS)}), "
                f"waiting {wait}s — {e}"
            )
            await asyncio.sleep(wait)


async def complete_with_fallback(messages: list[dict], config: LLMConfig) -> str:
    """Defines chat completion with retry + fallback chain."""
    from providers.openai_provider import OpenAIProvider
    from providers.claude_provider import ClaudeProvider

    try:
        return await _with_retry(
            lambda: OpenAIProvider(config).complete(messages),
            "OpenAI",
        )
    except (openai.RateLimitError, anthropic.RateLimitError):
        logger.warning("OpenAI rate limited after all retries, falling back to Claude")
    except Exception as e:
        logger.warning(f"OpenAI failed ({e}), falling back to Claude")

    return await _with_retry(
        lambda: ClaudeProvider(config).complete(messages),
        "Claude",
    )

