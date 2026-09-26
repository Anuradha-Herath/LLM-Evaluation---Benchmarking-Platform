import pytest
from datetime import datetime, timezone

from app.evaluators.result import EvaluationResult, EvaluationRun, EvaluationRunSummary
from app.schemas.regression import RegressionConfig
from app.services.regression_service import RegressionService


@pytest.fixture
def baseline_summary() -> EvaluationRunSummary:
    run = EvaluationRun(
        run_id="run-base",
        dataset_version="v1",
        provider="mock",
        model="mock-v1",
        prompt_version="v1",
        configuration={"temperature": 0.7},
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status="completed",
        total_cases=3,
        passed_cases=3,
        failed_cases=0,
    )
    results = [
        EvaluationResult(run_id="run-base", test_case_id="CASE-001", response="Text 1", latency_ms=50.0),
        EvaluationResult(run_id="run-base", test_case_id="CASE-002", response="Text 2", latency_ms=50.0),
        EvaluationResult(run_id="run-base", test_case_id="CASE-003", response="Text 3", latency_ms=50.0),
    ]
    return EvaluationRunSummary(run=run, results=results, avg_latency_ms=50.0, total_tokens=300)


def test_regression_pass(baseline_summary: EvaluationRunSummary):
    """Test candidate meeting all thresholds yields PASS status."""
    cand_summary = baseline_summary  # identical summary
    config = RegressionConfig(min_pass_rate_pct=70.0, max_avg_latency_ms=100.0)

    report = RegressionService.evaluate_regression(
        baseline_summary=baseline_summary,
        candidate_summary=cand_summary,
        config=config,
    )

    assert report.status == "PASS"
    assert len(report.violations) == 0


def test_regression_fail_latency(baseline_summary: EvaluationRunSummary):
    """Test candidate exceeding maximum latency yields FAIL status and violation."""
    cand_run = baseline_summary.run.model_copy()
    cand_results = baseline_summary.results
    cand_summary = EvaluationRunSummary(
        run=cand_run, results=cand_results, avg_latency_ms=500.0, total_tokens=300
    )

    config = RegressionConfig(max_avg_latency_ms=100.0)

    report = RegressionService.evaluate_regression(
        baseline_summary=baseline_summary,
        candidate_summary=cand_summary,
        config=config,
    )

    assert report.status == "FAIL"
    assert len(report.violations) >= 1
    assert any(v.metric_name == "avg_latency_ms" for v in report.violations)
    assert report.violations[0].baseline_value == 50.0
    assert report.violations[0].candidate_value == 500.0


def test_regression_fail_pass_rate_drop(baseline_summary: EvaluationRunSummary):
    """Test candidate experiencing pass rate drop yields FAIL status and isolates affected cases."""
    cand_run = EvaluationRun(
        run_id="run-cand",
        dataset_version="v1",
        provider="mock",
        model="mock-v2",
        prompt_version="v1",
        configuration={"temperature": 0.7},
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status="partial_failure",
        total_cases=3,
        passed_cases=1,
        failed_cases=2,
    )
    cand_results = [
        EvaluationResult(run_id="run-cand", test_case_id="CASE-001", response="Text 1", latency_ms=50.0),
        EvaluationResult(run_id="run-cand", test_case_id="CASE-002", response=None, error="Error in case 2"),
        EvaluationResult(run_id="run-cand", test_case_id="CASE-003", response=None, error="Error in case 3"),
    ]
    cand_summary = EvaluationRunSummary(run=cand_run, results=cand_results, avg_latency_ms=50.0, total_tokens=100)

    config = RegressionConfig(min_pass_rate_pct=80.0, max_allowed_pass_rate_drop_pct=5.0)

    report = RegressionService.evaluate_regression(
        baseline_summary=baseline_summary,
        candidate_summary=cand_summary,
        config=config,
    )

    assert report.status == "FAIL"
    assert len(report.violations) >= 1
    viol = report.violations[0]
    assert viol.baseline_value == 100.0
    assert viol.candidate_value == round(1 / 3 * 100.0, 2)
    assert "CASE-002" in viol.affected_cases
    assert "CASE-003" in viol.affected_cases
