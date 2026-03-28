"""Creates inference interface for the OpenAI API."""

from openai import AsyncOpenAI
from providers.base import LLMProvider
from config.settings import LLMConfig

class OpenAIProvider(LLMProvider):
    """Inherits LLMProvider as a base model for LLM inference through the OpenAI API."""
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = AsyncOpenAI()
    
    async def complete(self, messages: list[dict]) -> str:
        """Defines a asyncronous chat completion with AsyncOpenai.

        Args
            messages (list[dict]): messages list of dicts with role and content.

        Returns
            str: LLM chat completion with Assistant role.
        """
        response = await self.client.chat.completions.create(
            model=self.config.primary_model,
            messages=messages,
            timeout=self.config.timeout_seconds,
        )
        return response.choices[0].message.content
