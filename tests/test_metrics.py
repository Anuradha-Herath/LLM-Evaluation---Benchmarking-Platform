import pytest
from app.evaluators.metrics.base import MetricResult
from app.evaluators.metrics.classification import ClassificationMetric
from app.evaluators.metrics.exact_match import ContainsKeywordMetric, ExactMatchMetric
from app.evaluators.metrics.llm_judge import LLMJudgeMetric
from app.evaluators.metrics.registry import MetricRegistry
from app.evaluators.metrics.similarity import ResponseLengthMetric, TextSimilarityMetric
from app.evaluators.metrics.structured_output import JSONValidityMetric
from app.providers.mock_provider import MockProvider


@pytest.mark.asyncio
async def test_exact_match_metric():
    metric = ExactMatchMetric(case_sensitive=False, ignore_punctuation=True)
    res_pass = await metric.evaluate("Hello World!", reference_answer="hello world")
    assert res_pass.score == 1.0
    assert res_pass.passed is True

    res_fail = await metric.evaluate("Hello Universe", reference_answer="hello world")
    assert res_fail.score == 0.0
    assert res_fail.passed is False


@pytest.mark.asyncio
async def test_contains_keyword_metric():
    metric = ContainsKeywordMetric(default_keywords=["SaaS", "revenue"])
    res = await metric.evaluate("The SaaS company reported higher revenue in Q3.")
    assert res.score == 1.0
    assert res.passed is True

    res_partial = await metric.evaluate("The SaaS company grew quickly.")
    assert res_partial.score == 0.5
    assert res_partial.passed is False


@pytest.mark.asyncio
async def test_classification_metric_single_and_batch():
    metric = ClassificationMetric()
    res = await metric.evaluate("CRITICAL", reference_answer="CRITICAL")
    assert res.score == 1.0
    assert res.passed is True

    batch_metrics = ClassificationMetric.compute_batch_metrics(
        predictions=["CRITICAL", "LOW", "HIGH"],
        references=["CRITICAL", "LOW", "MEDIUM"],
    )
    assert batch_metrics["accuracy"] == round(2 / 3, 4)
    assert "precision" in batch_metrics
    assert "f1" in batch_metrics


@pytest.mark.asyncio
async def test_text_similarity_metric():
    metric = TextSimilarityMetric()
    res_high = await metric.evaluate(
        "SOC 2 Type 1 assesses security design at a point in time.",
        reference_answer="SOC 2 Type 1 report assesses security design at a point in time.",
    )
    assert res_high.score > 0.8
    assert res_high.passed is True

    res_low = await metric.evaluate(
        "Unrelated text about pizza delivery.",
        reference_answer="SOC 2 Type 1 report assesses security controls.",
    )
    assert res_low.score < 0.4
    assert res_low.passed is False


@pytest.mark.asyncio
async def test_response_length_metric():
    metric = ResponseLengthMetric(max_words=5)
    res_pass = await metric.evaluate("Three simple words")
    assert res_pass.score == 1.0
    assert res_pass.passed is True

    res_fail = await metric.evaluate("This is a much longer response than five words")
    assert res_fail.score == 0.0
    assert res_fail.passed is False


@pytest.mark.asyncio
async def test_json_validity_metric():
    metric = JSONValidityMetric(required_keys=["invoice_id", "amount"])
    
    valid_json = '```json\n{"invoice_id": "INV-100", "amount": 500.0}\n```'
    res_valid = await metric.evaluate(valid_json)
    assert res_valid.score == 1.0
    assert res_valid.passed is True

    missing_key_json = '{"invoice_id": "INV-100"}'
    res_missing = await metric.evaluate(missing_key_json)
    assert res_missing.score == 0.5
    assert res_missing.passed is False

    invalid_json = '{"invoice_id": "INV-100", amount:}'
    res_invalid = await metric.evaluate(invalid_json)
    assert res_invalid.score == 0.0
    assert res_invalid.passed is False


@pytest.mark.asyncio
async def test_llm_judge_metric():
    mock_judge_response = '{"score": 0.9, "reasoning": "Excellent clear response.", "passed": true}'
    mock_provider = MockProvider(mock_text=mock_judge_response)
    
    judge_metric = LLMJudgeMetric(judge_provider=mock_provider, judge_model="mock-judge")
    res = await judge_metric.evaluate(
        response_text="The server latency is 50ms.",
        expected_behavior="State low latency clearly.",
        user_input="What is server performance?",
    )

    assert res.metric_name == "llm_as_a_judge"
    assert res.score == 0.9
    assert res.passed is True
    assert res.reasoning == "Excellent clear response."
    assert res.judge_model == "mock-judge"


def test_metric_registry():
    factual_metrics = MetricRegistry.get_metrics_for_category("factual question")
    assert len(factual_metrics) >= 2
    metric_names = [m.name for m in factual_metrics]
    assert "exact_match" in metric_names
    assert "text_similarity" in metric_names
