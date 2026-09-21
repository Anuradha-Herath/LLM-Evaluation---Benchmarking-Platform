from abc import ABC, abstractmethod
import logging
import time
from typing import Any, Dict

from app.schemas.provider import LLMRequest, LLMResponse

logger = logging.getLogger("app.providers")


class BaseLLMProvider(ABC):
    """
    Abstract Base Class defining the contract for all LLM providers.
    Every LLM provider (OpenAI, Ollama, Anthropic, Mock) must implement this interface.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the canonical name of the provider."""
        pass

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Executes a prompt completion request against the LLM provider.

        :param request: Standardized LLMRequest object.
        :return: Standardized LLMResponse object.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verifies provider connection and availability.

        :return: True if service is healthy and reachable, False otherwise.
        """
        pass

    def _start_timer(self) -> float:
        """Returns the current high-resolution timestamp for latency calculation."""
        return time.perf_counter()

    def _calc_latency_ms(self, start_time: float) -> float:
        """Calculates elapsed time in milliseconds from start_time."""
        return round((time.perf_counter() - start_time) * 1000, 2)
