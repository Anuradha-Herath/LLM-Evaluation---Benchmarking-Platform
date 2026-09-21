import logging
from typing import Optional
import httpx

from app.core.config import settings
from app.core.exceptions import (
    LLMProviderAPIError,
    LLMProviderInvalidResponseError,
    LLMProviderRateLimitError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)
from app.providers.base import BaseLLMProvider
from app.schemas.provider import LLMRequest, LLMResponse

logger = logging.getLogger("app.providers.openai")


class OpenAIProvider(BaseLLMProvider):
    """
    LLM Provider implementation for OpenAI and OpenAI-compatible REST APIs.
    Communicates via standard /chat/completions endpoint using httpx.AsyncClient.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self._api_key = api_key or settings.OPENAI_API_KEY
        self._base_url = (base_url or settings.OPENAI_BASE_URL).rstrip("/")
        self._client = client

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        start_time = self._start_timer()

        headers = {
            "Content-Type": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.user_prompt})

        payload = {
            "model": request.model,
            "messages": messages,
            "temperature": request.config.temperature,
            "top_p": request.config.top_p,
            "frequency_penalty": request.config.frequency_penalty,
            "presence_penalty": request.config.presence_penalty,
        }

        if request.config.max_tokens:
            payload["max_tokens"] = request.config.max_tokens
        if request.config.stop:
            payload["stop"] = request.config.stop

        # Merge provider-specific extra parameters
        payload.update(request.config.extra_params)

        endpoint = f"{self._base_url}/chat/completions"
        timeout = request.config.timeout_seconds

        logger.info(
            f"Sending OpenAI completion request to {endpoint} (model={request.model})"
        )

        try:
            if self._client is not None:
                response = await self._client.post(
                    endpoint, json=payload, headers=headers, timeout=timeout
                )
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        endpoint, json=payload, headers=headers, timeout=timeout
                    )
        except httpx.TimeoutException as exc:
            logger.error(f"OpenAI provider request timed out: {exc}")
            raise LLMProviderTimeoutError(
                f"Request to OpenAI endpoint timed out after {timeout}s",
                provider_name=self.provider_name,
                model_name=request.model,
            ) from exc
        except httpx.RequestError as exc:
            logger.error(f"OpenAI endpoint unreachable: {exc}")
            raise LLMProviderUnavailableError(
                f"Unable to connect to OpenAI endpoint at {self._base_url}: {exc}",
                provider_name=self.provider_name,
                model_name=request.model,
            ) from exc

        latency_ms = self._calc_latency_ms(start_time)

        if response.status_code == 429:
            logger.warning("OpenAI rate limit exceeded (429).")
            raise LLMProviderRateLimitError(
                "OpenAI API rate limit exceeded.",
                provider_name=self.provider_name,
                model_name=request.model,
            )

        if response.status_code != 200:
            logger.error(
                f"OpenAI API error status code {response.status_code}: {response.text}"
            )
            raise LLMProviderAPIError(
                f"OpenAI API returned error code {response.status_code}: {response.text}",
                status_code=response.status_code,
                provider_name=self.provider_name,
                model_name=request.model,
            )

        try:
            data = response.json()
            choice = data["choices"][0]
            text = choice["message"]["content"]
            finish_reason = choice.get("finish_reason")
            usage = data.get("usage", {})

            input_tokens = usage.get("prompt_tokens")
            output_tokens = usage.get("completion_tokens")
            total_tokens = usage.get("total_tokens")

            return LLMResponse(
                text=text,
                model=request.model,
                provider_name=self.provider_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                finish_reason=finish_reason,
                metadata={
                    "system_fingerprint": data.get("system_fingerprint"),
                    "raw_usage": usage,
                },
            )
        except (KeyError, IndexError, ValueError) as exc:
            logger.error(f"Failed to parse OpenAI response: {exc}")
            raise LLMProviderInvalidResponseError(
                f"Invalid or missing fields in OpenAI response payload: {exc}",
                provider_name=self.provider_name,
                model_name=request.model,
            ) from exc

    async def health_check(self) -> bool:
        """
        Checks connectivity to OpenAI models endpoint.
        """
        endpoint = f"{self._base_url}/models"
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            if self._client is not None:
                resp = await self._client.get(endpoint, headers=headers, timeout=5.0)
            else:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(endpoint, headers=headers, timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False
