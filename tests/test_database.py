import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.repositories.experiment_repository import ExperimentRepository
from app.evaluators.metrics.base import MetricResult
from app.evaluators.result import EvaluationResult, EvaluationRun, EvaluationRunSummary
from app.models.base import Base


@pytest.fixture
def db_session():
    """In-memory SQLite Session fixture for database testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_save_and_retrieve_evaluation_run(db_session: Session):
    repo = ExperimentRepository(db_session)

    run_meta = EvaluationRun(
        run_id="test-run-101",
        dataset_version="v1",
        provider="mock",
        model="mock-gpt4",
        prompt_version="v1",
        configuration={"temperature": 0.7},
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status="completed",
        total_cases=2,
        passed_cases=1,
        failed_cases=1,
    )

    res_pass = EvaluationResult(
        run_id="test-run-101",
        test_case_id="CASE-001",
        response="Valid response text",
        latency_ms=45.5,
        input_tokens=10,
        output_tokens=15,
        total_tokens=25,
    )

    res_fail = EvaluationResult(
        run_id="test-run-101",
        test_case_id="CASE-002",
        response=None,
        latency_ms=0.0,
        error="LLMProviderTimeoutError: Connection timed out",
    )

    summary = EvaluationRunSummary(
        run=run_meta,
        results=[res_pass, res_fail],
        avg_latency_ms=22.75,
        total_input_tokens=10,
        total_output_tokens=15,
        total_tokens=25,
    )

    metric_map = {
        "CASE-001": [
            MetricResult(
                metric_name="exact_match",
                metric_version="1.0.0",
                score=1.0,
                passed=True,
                reasoning="Matched",
            )
        ]
    }

    # 1. Save Run & Results
    run_db = repo.save_evaluation_run_sync(summary, metric_results_map=metric_map)
    assert run_db.run_id == "test-run-101"

    # 2. Retrieve Run by ID
    retrieved_run = repo.get_run_by_id_sync("test-run-101")
    assert retrieved_run is not None
    assert retrieved_run.model == "mock-gpt4"
    assert retrieved_run.total_cases == 2
    assert retrieved_run.failed_cases == 1
    assert len(retrieved_run.results) == 2

    # 3. Retrieve Case Results
    results_list = repo.get_run_results_sync("test-run-101")
    assert len(results_list) == 2
    failed_case = next(r for r in results_list if r.case_id == "CASE-002")
    assert failed_case.error == "LLMProviderTimeoutError: Connection timed out"

    # 4. Retrieve Metrics
    passed_case = next(r for r in results_list if r.case_id == "CASE-001")
    metrics_list = repo.get_metrics_for_result_sync(passed_case.id)
    assert len(metrics_list) == 1
    assert metrics_list[0].metric_name == "exact_match"
    assert metrics_list[0].score == 1.0
