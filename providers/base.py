"""Creates ABC for LLM provider with completion function"""

import asyncio
import logging
from abc import ABC, abstractmethod

import anthropic
import openai

from config.settings import LLMConfig

logger = logging.getLogger(__name__)

_RETRY_WAITS = [30, 60, 120]  # seconds between retries on rate limit


class _RateLimiter:
    """Token bucket: allows at most `max_calls` per `period` seconds."""

    def __init__(self, max_calls: int, period: float = 60.0):
        self._max = max_calls
        self._period = period
        self._timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            import time
            now = time.monotonic()
            # drop timestamps outside the window
            self._timestamps = [t for t in self._timestamps if now - t < self._period]
            if len(self._timestamps) >= self._max:
                wait = self._period - (now - self._timestamps[0])
                logger.info(f"Rate limiter: {len(self._timestamps)} calls in window, waiting {wait:.1f}s")
                await asyncio.sleep(wait)
                now = time.monotonic()
                self._timestamps = [t for t in self._timestamps if now - t < self._period]
            self._timestamps.append(time.monotonic())


# Module-level limiters — recreated lazily from config on first use
_openai_limiter: "_RateLimiter | None" = None
_claude_limiter: "_RateLimiter | None" = None


def _get_limiters(config: "LLMConfig") -> tuple["_RateLimiter", "_RateLimiter"]:
    global _openai_limiter, _claude_limiter
    if _openai_limiter is None:
        _openai_limiter = _RateLimiter(max_calls=config.rpm_openai)
    if _claude_limiter is None:
        _claude_limiter = _RateLimiter(max_calls=config.rpm_claude)
    return _openai_limiter, _claude_limiter


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


async def complete_with_fallback(messages: list[dict], config: LLMConfig) -> tuple[str, str]:
    """Defines chat completion with retry + fallback chain. Returns (text, model_name)."""
    from providers.openai_provider import OpenAIProvider
    from providers.claude_provider import ClaudeProvider

    openai_lim, claude_lim = _get_limiters(config)

    if config.inter_call_delay > 0:
        await asyncio.sleep(config.inter_call_delay)

    try:
        await openai_lim.acquire()
        text = await _with_retry(
            lambda: OpenAIProvider(config).complete(messages),
            "OpenAI",
        )
        return text, config.primary_model
    except (openai.RateLimitError, anthropic.RateLimitError):
        logger.warning("OpenAI rate limited after all retries, falling back to Claude")
    except Exception as e:
        logger.warning(f"OpenAI failed ({e}), falling back to Claude")

    await claude_lim.acquire()
    text = await _with_retry(
        lambda: ClaudeProvider(config).complete(messages),
        "Claude",
    )
    return text, config.fallback_model

