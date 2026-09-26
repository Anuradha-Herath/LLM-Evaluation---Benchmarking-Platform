from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.db.repositories.experiment_repository import ExperimentRepository
from app.db.session import SyncSessionLocal
from app.evaluators.engine import EvaluationEngine
from app.evaluators.metrics.base import MetricResult
from app.evaluators.metrics.registry import MetricRegistry
from app.evaluators.result import EvaluationRunSummary
from app.schemas.api import EvaluationCreateRequest, PaginatedResponse
from app.schemas.dataset import BenchmarkDataset
from app.schemas.provider import GenerationConfig
from app.services.dataset_loader import DatasetLoader

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


@router.post(
    "",
    response_model=EvaluationRunSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger an Evaluation Run",
    description="Executes a benchmark dataset against a target LLM provider and evaluates metric results.",
)
async def create_evaluation(req: EvaluationCreateRequest) -> EvaluationRunSummary:
    dataset_path = Path(req.dataset_path)
    if not dataset_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset file not found at path '{req.dataset_path}'",
        )

    engine = EvaluationEngine(
        dataset_path=dataset_path,
        provider_name=req.provider,
        model=req.model,
        system_prompt=req.system_prompt,
        config=GenerationConfig(temperature=req.temperature),
        concurrency=req.concurrency,
    )

    summary: EvaluationRunSummary = await engine.execute()

    # Load dataset records to evaluate category-specific metrics
    if dataset_path.suffix.lower() == ".csv":
        dataset: BenchmarkDataset = DatasetLoader.load_from_csv(dataset_path)
    else:
        dataset = DatasetLoader.load_from_json(dataset_path)

    record_map = {r.id: r for r in dataset.records}
    metric_results_map: Dict[str, List[MetricResult]] = {}

    for res in summary.results:
        rec = record_map.get(res.test_case_id)
        cat = rec.category.value if rec else "default"
        metrics = MetricRegistry.get_metrics_for_category(cat)

        eval_scores: List[MetricResult] = []
        for m in metrics:
            score_obj = await m.evaluate(
                response_text=res.response or "",
                reference_answer=rec.reference_answer if rec else None,
                expected_behavior=rec.expected_behavior if rec else None,
                user_input=rec.input if rec else None,
            )
            eval_scores.append(score_obj)
        metric_results_map[res.test_case_id] = eval_scores

    if req.persist_db:
        try:
            with SyncSessionLocal() as session:
                repo = ExperimentRepository(session)
                repo.save_evaluation_run_sync(summary, metric_results_map=metric_results_map)
        except Exception as exc:
            # Non-fatal DB error logging
            pass

    return summary


@router.get(
    "",
    response_model=PaginatedResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List Evaluation Runs",
    description="Retrieves a paginated list of historical evaluation runs.",
)
async def list_evaluations(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[Dict[str, Any]]:
    with SyncSessionLocal() as session:
        from sqlalchemy import select
        from app.models.evaluation import EvaluationRunDB

        stmt = select(EvaluationRunDB).order_by(EvaluationRunDB.started_at.desc()).offset(offset).limit(limit)
        runs_db = list(session.execute(stmt).scalars().all())

        count_stmt = select(EvaluationRunDB)
        total = len(list(session.execute(count_stmt).scalars().all()))

        items = [
            {
                "run_id": r.run_id,
                "dataset_version": r.dataset_version,
                "provider": r.provider,
                "model": r.model,
                "status": r.status,
                "total_cases": r.total_cases,
                "passed_cases": r.passed_cases,
                "failed_cases": r.failed_cases,
                "started_at": r.started_at,
                "completed_at": r.completed_at,
            }
            for r in runs_db
        ]

        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{run_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get Evaluation Run Metadata",
    description="Retrieves detailed metadata for a single evaluation run by run_id.",
)
async def get_evaluation_run(run_id: str) -> Dict[str, Any]:
    with SyncSessionLocal() as session:
        repo = ExperimentRepository(session)
        run_db = repo.get_run_by_id_sync(run_id)

        if not run_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation run '{run_id}' not found.",
            )

        return {
            "run_id": run_db.run_id,
            "dataset_version": run_db.dataset_version,
            "provider": run_db.provider,
            "model": run_db.model,
            "prompt_version": run_db.prompt_version,
            "configuration": run_db.configuration,
            "status": run_db.status,
            "total_cases": run_db.total_cases,
            "passed_cases": run_db.passed_cases,
            "failed_cases": run_db.failed_cases,
            "started_at": run_db.started_at,
            "completed_at": run_db.completed_at,
        }


@router.get(
    "/{run_id}/results",
    response_model=PaginatedResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get Evaluation Run Results",
    description="Retrieves paginated case-by-case outputs for an evaluation run.",
)
async def get_evaluation_results(
    run_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[Dict[str, Any]]:
    with SyncSessionLocal() as session:
        repo = ExperimentRepository(session)
        run_db = repo.get_run_by_id_sync(run_id)
        if not run_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation run '{run_id}' not found.",
            )

        all_results = repo.get_run_results_sync(run_id)
        total = len(all_results)
        page_results = all_results[offset : offset + limit]

        items = [
            {
                "case_id": r.case_id,
                "response_text": r.response_text,
                "latency_ms": r.latency_ms,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "total_tokens": r.total_tokens,
                "error": r.error,
                "timestamp": r.timestamp,
            }
            for r in page_results
        ]

        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{run_id}/metrics",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get Evaluation Metrics for Run",
    description="Retrieves all computed metric evaluations for cases in a run.",
)
async def get_evaluation_metrics(run_id: str) -> List[Dict[str, Any]]:
    with SyncSessionLocal() as session:
        repo = ExperimentRepository(session)
        run_db = repo.get_run_by_id_sync(run_id)
        if not run_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation run '{run_id}' not found.",
            )

        results = repo.get_run_results_sync(run_id)
        metrics_list = []

        for r in results:
            for m in r.metric_results:
                metrics_list.append({
                    "case_id": r.case_id,
                    "metric_name": m.metric_name,
                    "metric_version": m.metric_version,
                    "score": m.score,
                    "passed": m.passed,
                    "reasoning": m.reasoning,
                    "judge_model": m.judge_model,
                })

        return metrics_list


@router.get(
    "/{run_id}/failures",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get Evaluation Run Failures",
    description="Retrieves cases that produced errors or failed quality thresholds in a run.",
)
async def get_evaluation_failures(run_id: str) -> List[Dict[str, Any]]:
    with SyncSessionLocal() as session:
        repo = ExperimentRepository(session)
        run_db = repo.get_run_by_id_sync(run_id)
        if not run_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation run '{run_id}' not found.",
            )

        results = repo.get_run_results_sync(run_id)
        failures = []

        for r in results:
            if r.error or any(m.passed is False for m in r.metric_results):
                failures.append({
                    "case_id": r.case_id,
                    "response_text": r.response_text,
                    "latency_ms": r.latency_ms,
                    "error": r.error,
                    "failed_metrics": [
                        {"metric_name": m.metric_name, "score": m.score, "reasoning": m.reasoning}
                        for m in r.metric_results
                        if m.passed is False
                    ],
                })

        return failures
