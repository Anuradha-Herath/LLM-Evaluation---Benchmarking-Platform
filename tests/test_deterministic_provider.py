import pytest
from app.core.exceptions import LLMProviderAPIError
from app.providers.deterministic_provider import DeterministicTestProvider
from app.providers.factory import ProviderFactory
from app.schemas.provider import LLMRequest


@pytest.mark.asyncio
async def test_deterministic_provider_registration():
    provider = ProviderFactory.get_provider("deterministic")
    assert isinstance(provider, DeterministicTestProvider)
    assert provider.provider_name == "deterministic"
    assert await provider.health_check() is True


@pytest.mark.asyncio
async def test_deterministic_provider_perfect_mode():
    provider = DeterministicTestProvider(mode="perfect", simulated_delay_ms=1.0)
    
    # Test JSON extraction
    req = LLMRequest(model="perfect", user_prompt="Extract INV-2026-889 invoice details")
    resp = await provider.generate(req)
    assert resp.model == "perfect"
    assert resp.provider_name == "deterministic"
    assert "INV-2026-889" in resp.text
    assert resp.total_tokens > 0

    # Test classification
    req2 = LLMRequest(model="perfect", user_prompt="Classify customer sentiment")
    resp2 = await provider.generate(req2)
    assert "NEGATIVE" in resp2.text


@pytest.mark.asyncio
async def test_deterministic_provider_degraded_mode():
    provider = DeterministicTestProvider(mode="degraded", simulated_delay_ms=1.0)
    req = LLMRequest(model="degraded", user_prompt="Summarize customer request.")
    resp = await provider.generate(req)
    assert "Degraded incomplete answer" in resp.text


@pytest.mark.asyncio
async def test_deterministic_provider_error_mode():
    provider = DeterministicTestProvider(mode="error", simulated_delay_ms=1.0)
    req = LLMRequest(model="error", user_prompt="Any prompt")
    with pytest.raises(LLMProviderAPIError) as exc_info:
        await provider.generate(req)
    assert "Simulated deterministic provider failure" in str(exc_info.value)


@pytest.mark.asyncio
async def test_deterministic_provider_repeatability():
    provider1 = DeterministicTestProvider(mode="perfect", simulated_delay_ms=1.0)
    provider2 = DeterministicTestProvider(mode="perfect", simulated_delay_ms=1.0)
    
    req = LLMRequest(model="perfect", user_prompt="What is ISO 20022?")
    resp1 = await provider1.generate(req)
    resp2 = await provider2.generate(req)
    
    assert resp1.text == resp2.text
    assert resp1.input_tokens == resp2.input_tokens
    assert resp1.output_tokens == resp2.output_tokens
