import logging
from typing import Optional
import httpx

from app.core.config import settings
from app.providers.openai_provider import OpenAIProvider

logger = logging.getLogger("app.providers.groq")


class GroqProvider(OpenAIProvider):
    """
    LLM Provider implementation for GroqCloud high-throughput inference (Llama, Mixtral, Gemma).
    Communicates via Groq's OpenAI-compatible REST endpoint.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        key = api_key or settings.GROQ_API_KEY
        url = base_url or settings.GROQ_BASE_URL
        super().__init__(api_key=key, base_url=url, client=client)

    @property
    def provider_name(self) -> str:
        return "groq"
