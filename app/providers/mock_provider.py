import asyncio
from typing import Optional

from app.providers.base import BaseLLMProvider
from app.schemas.provider import LLMRequest, LLMResponse


class MockProvider(BaseLLMProvider):
    """
    Deterministic Mock LLM Provider for offline testing and development.
    Simulates token counts, configurable latency delay, and echo responses.
    """

    def __init__(
        self,
        mock_text: Optional[str] = None,
        simulated_delay_sec: float = 0.05,
    ):
        self._mock_text = mock_text
        self._simulated_delay_sec = simulated_delay_sec

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        start_time = self._start_timer()

        if self._simulated_delay_sec > 0:
            await asyncio.sleep(self._simulated_delay_sec)

        text = (
            self._mock_text
            or f"[MOCK RESPONSE from {request.model}]: Processed prompt '{request.user_prompt}'"
        )

        input_tokens = len(request.user_prompt.split()) + (
            len(request.system_prompt.split()) if request.system_prompt else 0
        )
        output_tokens = len(text.split())
        total_tokens = input_tokens + output_tokens

        latency_ms = self._calc_latency_ms(start_time)

        return LLMResponse(
            text=text,
            model=request.model,
            provider_name=self.provider_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            finish_reason="stop",
            metadata={"mock": True, "simulated_delay_sec": self._simulated_delay_sec},
        )

    async def health_check(self) -> bool:
        return True
