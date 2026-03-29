import json
import logging
import time

from openai import AsyncOpenAI

from config.settings import LLMConfig
from providers.base import LLMProvider
from providers.metrics import LLMCallMetrics

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = AsyncOpenAI()

    async def complete(self, messages: list[dict]) -> str:
        start = time.perf_counter()
        ttft_ms = None
        chunks: list[str] = []
        prompt_tokens = 0
        completion_tokens = 0

        stream = await self.client.chat.completions.create(
            model=self.config.primary_model,
            messages=messages,
            timeout=self.config.timeout_seconds,
            stream=True,
            stream_options={"include_usage": True},
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                if ttft_ms is None:
                    ttft_ms = (time.perf_counter() - start) * 1000
                chunks.append(chunk.choices[0].delta.content)
            if chunk.usage:
                prompt_tokens = chunk.usage.prompt_tokens
                completion_tokens = chunk.usage.completion_tokens

        metrics = LLMCallMetrics(
            provider="openai",
            model=self.config.primary_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=(time.perf_counter() - start) * 1000,
            ttft_ms=ttft_ms,
        )
        logger.info("llm_metrics %s", json.dumps(metrics.to_log_dict()))
        return "".join(chunks)
