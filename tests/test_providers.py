import pytest
import httpx
from unittest.mock import AsyncMock

from app.core.exceptions import (
    LLMProviderAPIError,
    LLMProviderInvalidResponseError,
    LLMProviderRateLimitError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)
from app.providers.factory import ProviderFactory
from app.providers.mock_provider import MockProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider
from app.schemas.provider import GenerationConfig, LLMRequest


@pytest.mark.asyncio
async def test_mock_provider():
    """Test MockProvider generation and health check."""
    provider = MockProvider(mock_text="Test answer", simulated_delay_sec=0.01)
    assert provider.provider_name == "mock"
    assert await provider.health_check() is True

    req = LLMRequest(model="test-model", user_prompt="Hello world")
    resp = await provider.generate(req)

    assert resp.text == "Test answer"
    assert resp.model == "test-model"
    assert resp.provider_name == "mock"
    assert resp.input_tokens == 2
    assert resp.output_tokens == 2
    assert resp.total_tokens == 4
    assert resp.latency_ms > 0
    assert resp.finish_reason == "stop"


@pytest.mark.asyncio
async def test_openai_provider_success():
    """Test OpenAIProvider with a mocked successful response."""
    mock_payload = {
        "choices": [
            {
                "message": {"content": "OpenAI generated text"},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25,
        },
        "system_fingerprint": "fp_123",
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_http_resp = httpx.Response(status_code=200, json=mock_payload)
    mock_client.post.return_value = mock_http_resp

    provider = OpenAIProvider(api_key="test-key", client=mock_client)
    req = LLMRequest(model="gpt-4o", user_prompt="Explain AI")

    resp = await provider.generate(req)

    assert resp.text == "OpenAI generated text"
    assert resp.provider_name == "openai"
    assert resp.input_tokens == 10
    assert resp.output_tokens == 15
    assert resp.total_tokens == 25
    assert resp.finish_reason == "stop"


@pytest.mark.asyncio
async def test_openai_provider_rate_limit():
    """Test OpenAIProvider 429 rate limit error handling."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = httpx.Response(status_code=429, text="Rate limit exceeded")

    provider = OpenAIProvider(api_key="test-key", client=mock_client)
    req = LLMRequest(model="gpt-4o", user_prompt="Hello")

    with pytest.raises(LLMProviderRateLimitError) as exc_info:
        await provider.generate(req)

    assert "rate limit" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_openai_provider_timeout():
    """Test OpenAIProvider timeout exception handling."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = httpx.TimeoutException("Connection timed out")

    provider = OpenAIProvider(api_key="test-key", client=mock_client)
    req = LLMRequest(model="gpt-4o", user_prompt="Hello")

    with pytest.raises(LLMProviderTimeoutError):
        await provider.generate(req)


@pytest.mark.asyncio
async def test_openai_provider_unavailable():
    """Test OpenAIProvider endpoint unavailable error handling."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = httpx.RequestError("DNS lookup failed")

    provider = OpenAIProvider(api_key="test-key", client=mock_client)
    req = LLMRequest(model="gpt-4o", user_prompt="Hello")

    with pytest.raises(LLMProviderUnavailableError):
        await provider.generate(req)


@pytest.mark.asyncio
async def test_ollama_provider_success():
    """Test OllamaProvider with a mocked successful response."""
    mock_payload = {
        "model": "llama3",
        "message": {"role": "assistant", "content": "Ollama text response"},
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 8,
        "eval_count": 12,
        "total_duration": 500000000,
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = httpx.Response(status_code=200, json=mock_payload)

    provider = OllamaProvider(base_url="http://localhost:11434", client=mock_client)
    req = LLMRequest(model="llama3", user_prompt="Hello Ollama")

    resp = await provider.generate(req)

    assert resp.text == "Ollama text response"
    assert resp.provider_name == "ollama"
    assert resp.input_tokens == 8
    assert resp.output_tokens == 12
    assert resp.total_tokens == 20
    assert resp.finish_reason == "stop"


@pytest.mark.asyncio
async def test_ollama_provider_model_not_found():
    """Test OllamaProvider 404 model not found error handling."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = httpx.Response(status_code=404, text="model not found")

    provider = OllamaProvider(client=mock_client)
    req = LLMRequest(model="non-existent-model", user_prompt="Hello")

    with pytest.raises(LLMProviderAPIError) as exc_info:
        await provider.generate(req)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_provider_factory():
    """Test ProviderFactory creation and invalid key error."""
    mock_p = ProviderFactory.get_provider("mock")
    assert isinstance(mock_p, MockProvider)

    openai_p = ProviderFactory.get_provider("openai")
    assert isinstance(openai_p, OpenAIProvider)

    ollama_p = ProviderFactory.get_provider("ollama")
    assert isinstance(ollama_p, OllamaProvider)

    with pytest.raises(ValueError) as exc_info:
        ProviderFactory.get_provider("invalid_provider_type")

    assert "Unsupported provider" in str(exc_info.value)
