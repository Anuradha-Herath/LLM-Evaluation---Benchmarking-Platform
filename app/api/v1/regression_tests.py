from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

from app.schemas.api import RegressionTestApiRequest
from app.schemas.benchmark import BenchmarkConfig, ModelSpec, PromptSpec
from app.schemas.regression import RegressionConfig, RegressionReport
from app.services.benchmark_service import BenchmarkService
from app.services.regression_service import RegressionService

router = APIRouter(prefix="/regression-tests", tags=["Regression Tests"])


@router.post(
    "",
    response_model=RegressionReport,
    status_code=status.HTTP_200_OK,
    summary="Execute Regression Test",
    description="Compares Candidate model against Baseline model on a fixed benchmark dataset to detect regressions.",
)
async def run_regression_test(req: RegressionTestApiRequest) -> RegressionReport:
    dataset_path = Path(req.dataset_path)
    if not dataset_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset file not found at path '{req.dataset_path}'",
        )

    reg_config = RegressionConfig.model_validate(req.config) if req.config else RegressionConfig()

    base_parts = req.baseline_model.split(":")
    base_spec = ModelSpec(
        provider=base_parts[0],
        model=base_parts[1] if len(base_parts) > 1 else base_parts[0],
        label=f"Baseline ({req.baseline_model})",
    )

    cand_parts = req.candidate_model.split(":")
    cand_spec = ModelSpec(
        provider=cand_parts[0],
        model=cand_parts[1] if len(cand_parts) > 1 else cand_parts[0],
        label=f"Candidate ({req.candidate_model})",
    )

    prompt_spec = PromptSpec(name="Default Prompt", version="v1", system_prompt=None)

    bench_config = BenchmarkConfig(
        dataset_path=dataset_path,
        models=[base_spec, cand_spec],
        prompts=[prompt_spec],
        concurrency=5,
    )

    matrix_results = await BenchmarkService.run_benchmark_matrix(bench_config)
    base_summary, base_metric_map, _, _ = matrix_results[0]
    cand_summary, cand_metric_map, _, _ = matrix_results[1]

    return RegressionService.evaluate_regression(
        baseline_summary=base_summary,
        candidate_summary=cand_summary,
        baseline_metric_map=base_metric_map,
        candidate_metric_map=cand_metric_map,
        config=reg_config,
        baseline_label=base_spec.label,
        candidate_label=cand_spec.label,
    )


@router.post(
    "/{id}/run",
    response_model=RegressionReport,
    status_code=status.HTTP_200_OK,
    summary="Run Saved Regression Test Configuration",
    description="Executes a regression test using a saved configuration file or ID.",
)
async def run_saved_regression_test(id: str) -> RegressionReport:
    config_file = Path("experiments") / "regression_config.json"
    req = RegressionTestApiRequest(
        dataset_path="datasets/benchmark_v1.json",
        baseline_model="mock:mock-model-v1",
        candidate_model="mock:mock-model-v1",
    )
    return await run_regression_test(req)
