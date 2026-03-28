"""Creates inference interface for the Anthropic API."""

from anthropic import AsyncAnthropic
from providers.base import LLMProvider
from config.settings import LLMConfig

class ClaudeProvider(LLMProvider):
    """Inherits LLMProvider as a base model for LLM inference through the Anthropic API."""
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = AsyncAnthropic()
    
    async def complete(self, messages: list[dict]) -> str:
        """Defines a asyncronous chat completion with AsyncAnthropic.

        Args
            messages (list[dict]): messages list of dicts with role and content.

        Returns
            str: LLM chat completion with Assistant role.
        """
        system = next((m["content"] for m in messages if m["role"] =="system"), None)
        user_messages = [m for m in messages if m["role"] != "system"]

        kwargs: dict = {
            "model": self.config.fallback_model,
            "max_tokens": 4096,
            "messages": user_messages,
        }

        if system:
            kwargs["system"] = system

        response = await self.client.messages.create(**kwargs)
        return response.content[0].text