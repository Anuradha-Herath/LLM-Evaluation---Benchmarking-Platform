from typing import Any, Dict, Type

from app.providers.base import BaseLLMProvider
from app.providers.deterministic_provider import DeterministicTestProvider
from app.providers.mock_provider import MockProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider


class ProviderFactory:
    """
    Factory for creating and managing LLM Provider instances.
    """

    _registry: Dict[str, Type[BaseLLMProvider]] = {
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
        "mock": MockProvider,
        "deterministic": DeterministicTestProvider,
    }

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[BaseLLMProvider]) -> None:
        """
        Registers a custom provider implementation.
        """
        cls._registry[name.lower()] = provider_cls

    @classmethod
    def get_provider(cls, provider_type: str, **kwargs: Any) -> BaseLLMProvider:
        """
        Instantiates an LLM provider based on type name.

        :param provider_type: Provider string ('openai', 'ollama', 'mock').
        :param kwargs: Additional arguments passed to provider constructor.
        :return: Initialized BaseLLMProvider instance.
        """
        canonical_name = provider_type.lower()
        provider_cls = cls._registry.get(canonical_name)

        if not provider_cls:
            supported = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Unsupported provider type '{provider_type}'. Supported providers: [{supported}]"
            )

        return provider_cls(**kwargs)
