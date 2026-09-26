import logging
from typing import Optional

from app.core.config import settings
from app.observability.base import BaseObservability
from app.observability.langfuse import LangfuseObservability
from app.observability.noop import NoOpObservability

logger = logging.getLogger("app.observability.factory")


class ObservabilityFactory:
    """
    Factory for instantiating the appropriate Observability provider based on environment configuration.
    """

    _override_provider: Optional[BaseObservability] = None

    @classmethod
    def set_override(cls, provider: Optional[BaseObservability]) -> None:
        """Sets a temporary override provider instance (useful for unit testing)."""
        cls._override_provider = provider

    @classmethod
    def get_observability(cls) -> BaseObservability:
        """
        Returns the active Observability provider.
        If override is set, returns override.
        If LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set, returns LangfuseObservability.
        Otherwise returns NoOpObservability.
        """
        if cls._override_provider is not None:
            return cls._override_provider

        pub_key = settings.LANGFUSE_PUBLIC_KEY
        sec_key = settings.LANGFUSE_SECRET_KEY

        if pub_key and sec_key and pub_key.strip() and sec_key.strip():
            logger.info("Langfuse credentials detected in environment. Activating LangfuseObservability provider.")
            return LangfuseObservability(public_key=pub_key, secret_key=sec_key, host=settings.LANGFUSE_HOST)

        logger.debug("Langfuse credentials not set. Activating NoOpObservability provider.")
        return NoOpObservability()
