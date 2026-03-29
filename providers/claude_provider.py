import json
import logging
import time

from anthropic import AsyncAnthropic

from config.settings import LLMConfig
from providers.base import LLMProvider
from providers.metrics import LLMCallMetrics

logger = logging.getLogger(__name__)


class ClaudeProvider(LLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = AsyncAnthropic()

    async def complete(self, messages: list[dict]) -> str:
        system = next((m["content"] for m in messages if m["role"] == "system"), None)
        user_messages = [m for m in messages if m["role"] != "system"]

        kwargs: dict = {
            "model": self.config.fallback_model,
            "max_tokens": 4096,
            "messages": user_messages,
        }
        if system:
            kwargs["system"] = system

        start = time.perf_counter()
        ttft_ms = None
        chunks: list[str] = []

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                if ttft_ms is None and text:
                    ttft_ms = (time.perf_counter() - start) * 1000
                chunks.append(text)
            final = await stream.get_final_message()

        metrics = LLMCallMetrics(
            provider="anthropic",
            model=self.config.fallback_model,
            prompt_tokens=final.usage.input_tokens,
            completion_tokens=final.usage.output_tokens,
            latency_ms=(time.perf_counter() - start) * 1000,
            ttft_ms=ttft_ms,
        )
        logger.info("llm_metrics %s", json.dumps(metrics.to_log_dict()))
        return "".join(chunks)
