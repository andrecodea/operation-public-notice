"""Defines LLM inference configurations for data extraction and LLM-as-a-judge"""

from pydantic import BaseModel

class LLMConfig(BaseModel):
    primary_provider: str = "openai"
    primary_model: str = "gpt-4o"
    fallback_provider: str = "anthropic"
    fallback_model: str = "claude-sonnet-4-5"
    max_retries: int = 2
    timeout_seconds: int = 60
    correction_threshold: float = 0.6

