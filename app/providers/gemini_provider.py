import logging
from typing import Optional
import httpx

from app.core.config import settings
from app.providers.openai_provider import OpenAIProvider

logger = logging.getLogger("app.providers.gemini")


class GeminiProvider(OpenAIProvider):
    """
    LLM Provider implementation for Google Gemini models (Gemini 2.0 Flash, Gemini 1.5 Pro).
    Communicates via Google's OpenAI-compatible REST endpoint (v1beta/openai).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        key = api_key or settings.GEMINI_API_KEY
        url = base_url or settings.GEMINI_BASE_URL
        super().__init__(api_key=key, base_url=url, client=client)

    @property
    def provider_name(self) -> str:
        return "gemini"
