import logging
from typing import Optional
import httpx

from app.core.config import settings
from app.core.exceptions import (
    LLMProviderAPIError,
    LLMProviderInvalidResponseError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)
from app.providers.base import BaseLLMProvider
from app.schemas.provider import LLMRequest, LLMResponse

logger = logging.getLogger("app.providers.ollama")


class OllamaProvider(BaseLLMProvider):
    """
    LLM Provider implementation for Ollama local models via REST API (/api/chat).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self._base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._client = client

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        start_time = self._start_timer()

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.user_prompt})

        options = {
            "temperature": request.config.temperature,
            "top_p": request.config.top_p,
            "frequency_penalty": request.config.frequency_penalty,
            "presence_penalty": request.config.presence_penalty,
        }
        if request.config.max_tokens:
            options["num_predict"] = request.config.max_tokens
        if request.config.stop:
            options["stop"] = request.config.stop

        options.update(request.config.extra_params)

        payload = {
            "model": request.model,
            "messages": messages,
            "stream": False,
            "options": options,
        }

        endpoint = f"{self._base_url}/api/chat"
        timeout = request.config.timeout_seconds

        logger.info(
            f"Sending Ollama request to {endpoint} (model={request.model})"
        )

        try:
            if self._client is not None:
                response = await self._client.post(
                    endpoint, json=payload, timeout=timeout
                )
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        endpoint, json=payload, timeout=timeout
                    )
        except httpx.TimeoutException as exc:
            logger.error(f"Ollama provider request timed out: {exc}")
            raise LLMProviderTimeoutError(
                f"Request to Ollama endpoint timed out after {timeout}s",
                provider_name=self.provider_name,
                model_name=request.model,
            ) from exc
        except httpx.RequestError as exc:
            logger.error(f"Ollama service unreachable: {exc}")
            raise LLMProviderUnavailableError(
                f"Unable to connect to Ollama at {self._base_url}. Ensure Ollama is running locally.",
                provider_name=self.provider_name,
                model_name=request.model,
            ) from exc

        latency_ms = self._calc_latency_ms(start_time)

        if response.status_code == 404:
            logger.error(f"Ollama model '{request.model}' not found.")
            raise LLMProviderAPIError(
                f"Model '{request.model}' not found in local Ollama instance. Run 'ollama pull {request.model}' first.",
                status_code=404,
                provider_name=self.provider_name,
                model_name=request.model,
            )

        if response.status_code != 200:
            logger.error(
                f"Ollama API error status code {response.status_code}: {response.text}"
            )
            raise LLMProviderAPIError(
                f"Ollama returned error code {response.status_code}: {response.text}",
                status_code=response.status_code,
                provider_name=self.provider_name,
                model_name=request.model,
            )

        try:
            data = response.json()
            message_obj = data.get("message", {})
            text = message_obj.get("content", "")

            input_tokens = data.get("prompt_eval_count")
            output_tokens = data.get("eval_count")
            total_tokens = (
                (input_tokens + output_tokens)
                if (input_tokens is not None and output_tokens is not None)
                else None
            )

            finish_reason = data.get("done_reason") or ("stop" if data.get("done") else None)

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
                    "total_duration_ns": data.get("total_duration"),
                    "load_duration_ns": data.get("load_duration"),
                    "eval_duration_ns": data.get("eval_duration"),
                },
            )
        except (KeyError, ValueError) as exc:
            logger.error(f"Failed to parse Ollama response: {exc}")
            raise LLMProviderInvalidResponseError(
                f"Invalid response structure from Ollama: {exc}",
                provider_name=self.provider_name,
                model_name=request.model,
            ) from exc

    async def health_check(self) -> bool:
        """
        Checks connectivity to Ollama server endpoint.
        """
        endpoint = f"{self._base_url}/api/tags"
        try:
            if self._client is not None:
                resp = await self._client.get(endpoint, timeout=3.0)
            else:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(endpoint, timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False
