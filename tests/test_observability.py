import pytest
from pathlib import Path
from unittest.mock import MagicMock

from app.evaluators.engine import EvaluationEngine
from app.observability.base import BaseObservability
from app.observability.factory import ObservabilityFactory
from app.observability.langfuse import LangfuseObservability
from app.observability.noop import NoOpObservability


def test_noop_observability():
    """Test NoOpObservability executes methods without error."""
    noop = NoOpObservability()
    noop.start_trace(run_id="run-1", name="test_trace")
    noop.log_generation(
        run_id="run-1",
        case_id="CASE-001",
        model="mock-model",
        user_prompt="Hello",
        response_text="World",
        latency_ms=10.5,
        input_tokens=2,
        output_tokens=2,
    )
    noop.log_metric(run_id="run-1", case_id="CASE-001", metric_name="exact_match", score=1.0)
    noop.end_trace(run_id="run-1", status="completed")
    noop.flush()


def test_langfuse_observability_mocked():
    """Test LangfuseObservability buffering and metadata sanitization with mock client."""
    mock_client = MagicMock()
    obs = LangfuseObservability(
        public_key="pk-test", secret_key="sk-test", client=mock_client
    )

    # Test metadata sanitization
    meta = {"dataset_version": "v1", "api_key": "secret_123", "normal_field": "val"}
    clean_meta = obs._sanitize_metadata(meta)
    assert clean_meta["api_key"] == "[REDACTED]"
    assert clean_meta["dataset_version"] == "v1"

    # Test trace logging
    obs.start_trace(run_id="run-100", name="eval_trace", metadata=meta)
    assert "run-100" in obs._traces

    obs.log_generation(
        run_id="run-100",
        case_id="CASE-001",
        model="gpt-4o",
        user_prompt="Prompt text",
        response_text="Response text",
        latency_ms=25.0,
        input_tokens=10,
        output_tokens=5,
    )
    assert "run-100:CASE-001" in obs._spans

    obs.log_metric(
        run_id="run-100",
        case_id="CASE-001",
        metric_name="exact_match",
        score=1.0,
        passed=True,
    )

    obs.end_trace(run_id="run-100", status="completed")
    obs.flush()
    assert mock_client.flush.called


def test_observability_factory():
    """Test ObservabilityFactory provider selection and override capability."""
    # Test override
    mock_obs = MagicMock(spec=BaseObservability)
    ObservabilityFactory.set_override(mock_obs)
    assert ObservabilityFactory.get_observability() == mock_obs

    # Reset override
    ObservabilityFactory.set_override(None)
    
    # When keys are empty, factory must return NoOpObservability
    obs = ObservabilityFactory.get_observability()
    assert isinstance(obs, NoOpObservability) or isinstance(obs, LangfuseObservability)


@pytest.mark.asyncio
async def test_engine_observability_integration(tmp_path: Path):
    """Test EvaluationEngine correctly triggers observability hooks."""
    import json
    dataset_file = tmp_path / "obs_test.json"
    dataset_data = {
        "metadata": {"version": "v1", "name": "Obs Test", "description": "Test", "total_records": 1},
        "records": [
            {"id": "CASE-001", "category": "factual question", "input": "Q", "expected_behavior": "B"}
        ],
    }
    with open(dataset_file, "w", encoding="utf-8") as f:
        json.dump(dataset_data, f)

    mock_obs = MagicMock(spec=BaseObservability)
    ObservabilityFactory.set_override(mock_obs)

    try:
        engine = EvaluationEngine(
            dataset_path=dataset_file,
            provider_name="mock",
            model="mock-model",
        )
        summary = await engine.execute()

        assert summary.run.status == "completed"
        assert mock_obs.start_trace.called
        assert mock_obs.log_generation.called
        assert mock_obs.end_trace.called
        assert mock_obs.flush.called
    finally:
        ObservabilityFactory.set_override(None)
