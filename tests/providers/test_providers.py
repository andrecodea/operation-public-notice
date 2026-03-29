"""Tests provider inference capabilities, fallback chain, and LLM metrics."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from config.settings import LLMConfig
from providers.base import complete_with_fallback
from providers.metrics import LLMCallMetrics


@pytest.fixture
def config():
    return LLMConfig()


# ---------------------------------------------------------------------------
# Helpers para mocks de streaming
# ---------------------------------------------------------------------------

async def _openai_stream(*chunks):
    """Async generator que simula o stream de chunks do OpenAI."""
    for chunk in chunks:
        yield chunk


def _openai_chunk(content: str | None = None, prompt_tokens: int = 0, completion_tokens: int = 0):
    chunk = MagicMock()
    chunk.choices = [MagicMock(delta=MagicMock(content=content))] if content is not None else []
    chunk.usage = MagicMock(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens) if prompt_tokens else None
    return chunk


def _mock_anthropic_stream(text: str = "resposta claude", input_tokens: int = 10, output_tokens: int = 5):
    """Context manager mock que simula client.messages.stream(...)."""
    async def text_gen():
        yield text

    stream_obj = MagicMock()
    stream_obj.text_stream = text_gen()
    stream_obj.get_final_message = AsyncMock(return_value=MagicMock(
        usage=MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    ))

    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=stream_obj)
    ctx.__aexit__ = AsyncMock(return_value=None)
    return ctx


# ---------------------------------------------------------------------------
# Fallback chain
# ---------------------------------------------------------------------------

async def test_use_openai_when_available(config):
    with (
        patch("providers.openai_provider.AsyncOpenAI"),
        patch("providers.openai_provider.OpenAIProvider.complete",
              new=AsyncMock(return_value='{"ok": true}')),
    ):
        result = await complete_with_fallback([{"role": "user", "content": "teste"}], config)
    assert result == '{"ok": true}'


async def test_fallback_to_claude(config):
    with (
        patch("providers.openai_provider.OpenAIProvider.complete",
              new=AsyncMock(side_effect=Exception("rate limit"))),
        patch("providers.claude_provider.ClaudeProvider.complete",
              new=AsyncMock(return_value='{"fallback": true}')),
    ):
        result = await complete_with_fallback([{"role": "user", "content": "teste"}], config)
    assert result == '{"fallback": true}'


# ---------------------------------------------------------------------------
# OpenAI provider — streaming
# ---------------------------------------------------------------------------

async def test_openai_provider_uses_primary_model(config):
    from providers.openai_provider import OpenAIProvider

    stream = _openai_stream(
        _openai_chunk(content="resposta"),
        _openai_chunk(prompt_tokens=10, completion_tokens=3),
    )
    with patch("providers.openai_provider.AsyncOpenAI") as MockClient:
        MockClient.return_value.chat.completions.create = AsyncMock(return_value=stream)
        provider = OpenAIProvider(config)
        result = await provider.complete([{"role": "user", "content": "teste"}])

    call_kwargs = MockClient.return_value.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == config.primary_model
    assert result == "resposta"


# ---------------------------------------------------------------------------
# Claude provider — streaming
# ---------------------------------------------------------------------------

async def test_claude_uses_fallback_model(config):
    from providers.claude_provider import ClaudeProvider

    with patch("providers.claude_provider.AsyncAnthropic") as MockClient:
        MockClient.return_value.messages.stream.return_value = _mock_anthropic_stream("resposta claude")
        provider = ClaudeProvider(config)
        result = await provider.complete([{"role": "user", "content": "teste"}])

    call_kwargs = MockClient.return_value.messages.stream.call_args.kwargs
    assert call_kwargs["model"] == config.fallback_model
    assert result == "resposta claude"


# ---------------------------------------------------------------------------
# LLMCallMetrics
# ---------------------------------------------------------------------------

def test_metrics_total_tokens():
    m = LLMCallMetrics(provider="openai", model="gpt-4o", prompt_tokens=100, completion_tokens=50)
    assert m.total_tokens == 150


def test_metrics_to_log_dict_rounds_floats():
    m = LLMCallMetrics(provider="openai", model="gpt-4o",
                       latency_ms=1234.5678, ttft_ms=432.1)
    d = m.to_log_dict()
    assert d["latency_ms"] == 1234.6
    assert d["ttft_ms"] == 432.1


def test_metrics_ttft_none_stays_none():
    m = LLMCallMetrics(provider="openai", model="gpt-4o")
    assert m.to_log_dict()["ttft_ms"] is None
