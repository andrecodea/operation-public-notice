"""Creates ABC for LLM provider with completion function"""

import logging
from abc import ABC, abstractmethod
from config.settings import LLMConfig

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Initializes ABC for providers with a chat completion abstract method."""
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    async def complete(self, messages: list[dict]) -> str: ...

async def complete_with_fallback(messages: list[dict], config: LLMConfig) -> str:
    """Defines chat completion with fallback chain."""
    from providers.openai_provider import OpenAIProvider
    from providers.claude_provider import ClaudeProvider
    try:
        return await OpenAIProvider(config).complete(messages)
    except Exception as e:
        logger.warning(f"OpenAI falhou ({e}), usando Claude como fallback")
        return await ClaudeProvider(config).complete(messages)

