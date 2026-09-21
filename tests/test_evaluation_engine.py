import pytest
from pathlib import Path
from unittest.mock import AsyncMock

from app.core.exceptions import LLMProviderTimeoutError
from app.evaluators.engine import EvaluationEngine
from app.evaluators.result import EvaluationRunSummary
from app.evaluators.runner import CaseRunner
from app.providers.base import BaseLLMProvider
from app.providers.mock_provider import MockProvider
from app.schemas.dataset import DatasetCategory, DatasetRecord, DifficultyLevel
from app.schemas.provider import LLMRequest, LLMResponse


@pytest.fixture
def dataset_file(tmp_path: Path) -> Path:
    """Create a temporary dataset JSON file with 5 records."""
    data = {
        "metadata": {"version": "v1", "name": "Test Set", "description": "Test", "total_records": 5},
        "records": [
            {
                "id": f"TEST-{i:03d}",
                "category": "factual question",
                "input": f"Question {i}",
                "expected_behavior": f"Behavior {i}",
            }
            for i in range(1, 6)
        ],
    }
    file_path = tmp_path / "test_benchmark.json"
    import json
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return file_path


@pytest.mark.asyncio
async def test_evaluation_engine_mock_success(dataset_file: Path):
    """Test full EvaluationEngine run with MockProvider."""
    engine = EvaluationEngine(
        dataset_path=dataset_file,
        provider_name="mock",
        model="mock-gpt4",
        concurrency=2,
    )

    summary = await engine.execute()

    assert isinstance(summary, EvaluationRunSummary)
    assert summary.run.status == "completed"
    assert summary.run.total_cases == 5
    assert summary.run.passed_cases == 5
    assert summary.run.failed_cases == 0
    assert summary.avg_latency_ms > 0
    assert summary.total_tokens > 0
    assert len(summary.results) == 5


@pytest.mark.asyncio
async def test_case_runner_fault_tolerance():
    """Test CaseRunner catches provider timeouts and isolates errors."""
    mock_provider = AsyncMock(spec=BaseLLMProvider)
    mock_provider.generate.side_effect = LLMProviderTimeoutError("Connection timeout")

    record = DatasetRecord(
        id="FAIL-001",
        category=DatasetCategory.REASONING,
        input="Hard question",
        expected_behavior="Valid answer",
        difficulty=DifficultyLevel.HARD,
    )

    result = await CaseRunner.run_case(
        run_id="run-test-123",
        record=record,
        provider=mock_provider,
        model="test-model",
        max_retries=1,
        initial_backoff_sec=0.01,
    )

    assert result.test_case_id == "FAIL-001"
    assert result.response is None
    assert result.error is not None
    assert "LLMProviderTimeoutError" in result.error


@pytest.mark.asyncio
async def test_evaluation_engine_partial_failure(dataset_file: Path):
    """Test EvaluationEngine handles mixed success/failure cases gracefully."""
    class FlakyProvider(BaseLLMProvider):
        @property
        def provider_name(self) -> str:
            return "flaky"

        async def generate(self, request: LLMRequest) -> LLMResponse:
            if "Question 2" in request.user_prompt:
                raise LLMProviderTimeoutError("Timeout on question 2")
            return LLMResponse(
                text="Success",
                model=request.model,
                provider_name="flaky",
                input_tokens=5,
                output_tokens=5,
                total_tokens=10,
                latency_ms=10.0,
            )

        async def health_check(self) -> bool:
            return True

    from app.providers.factory import ProviderFactory
    ProviderFactory.register_provider("flaky", FlakyProvider)

    engine = EvaluationEngine(
        dataset_path=dataset_file,
        provider_name="flaky",
        model="flaky-model",
        concurrency=2,
    )

    summary = await engine.execute()

    assert summary.run.status == "partial_failure"
    assert summary.run.total_cases == 5
    assert summary.run.passed_cases == 4
    assert summary.run.failed_cases == 1
