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
    rpm_openai: int = 50   # requests per minute ceiling for OpenAI
    rpm_claude: int = 40   # requests per minute ceiling for Claude
    inter_call_delay: float = 3.0  # seconds to wait between LLM calls (reduces TPM bursts)

