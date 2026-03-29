"""Tests provider inference capabilites and fallback chain"""

import pytest 
from unittest.mock import AsyncMock, MagicMock, patch
from config.settings import LLMConfig
from providers.base import complete_with_fallback

@pytest.fixture
def config():
    return LLMConfig()

async def test_use_openai_when_available(config):
    """Asserts that OpenAI is used when available."""
    with patch("providers.openai_provider.AsyncOpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create = AsyncMock(
            return_value=MagicMock(choices=[MagicMock(message=MagicMock(content='{"ok": true}'))])
        )
        result = await complete_with_fallback([{"role": "user", "content": "teste"}], config)
        assert result == '{"ok": true}'

async def test_fallback_to_claude(config):
    """Asserts that fallback happens if OpenAI fails."""
    with (
        patch("providers.openai_provider.AsyncOpenAI") as MockOpenAI,
        patch("providers.claude_provider.AsyncAnthropic") as MockClaude,
    ):
        MockOpenAI.return_value.chat.completions.create = AsyncMock(side_effect=Exception("rate limit"))
        MockClaude.return_value.messages.create = AsyncMock(
            return_value=MagicMock(content=[MagicMock(text='{"fallback": true}')])
        )
        result = await complete_with_fallback([{"role": "user", "content": "teste"}], config)
        assert result == '{"fallback": true}'

async def test_openai_provider_uses_primary_model(config):
    """Asserts that OpenAI uses the predefined primary model (gpt-4o)."""
    from providers.openai_provider import OpenAIProvider
    with patch("providers.openai_provider.AsyncOpenAI") as MockClient:
        MockClient.return_value.chat.completions.create = AsyncMock(
            return_value=AsyncMock(choices=[
                AsyncMock(message=AsyncMock(content="resposta"))
            ])
        )
        provider = OpenAIProvider(config)
        result = await provider.complete([{"role":"user", "content":"teste"}])
    call_kwargs = MockClient.return_value.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == config.primary_model
    assert result == "resposta"

async def test_claude_uses_fallback_model(config):
    """Asserts that Claude uses the predefined fallback model (claude-sonnet-4-5)."""
    from providers.claude_provider import ClaudeProvider
    with patch("providers.claude_provider.AsyncAnthropic") as MockClient:
        MockClient.return_value.messages.create = AsyncMock(
            return_value=AsyncMock(content=[AsyncMock(text="resposta claude")])
        )
        provider = ClaudeProvider(config)
        result = await provider.complete([{"role":"user", "content":"teste"}])
        call_kwargs = MockClient.return_value.messages.create.call_args.kwargs
        assert call_kwargs["model"] == config.fallback_model
        assert result == "resposta claude"

# To run: uv run pytest tests/providers/ -v
# PASSED: 28/03/2026