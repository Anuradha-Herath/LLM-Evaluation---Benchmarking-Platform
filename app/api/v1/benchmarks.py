from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

from app.schemas.api import BenchmarkCreateRequest
from app.schemas.benchmark import BenchmarkComparisonReport, BenchmarkConfig, ModelSpec, PromptSpec
from app.services.benchmark_service import BenchmarkService
from app.services.comparison_service import ComparisonService

router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])


@router.post(
    "",
    response_model=BenchmarkComparisonReport,
    status_code=status.HTTP_201_CREATED,
    summary="Execute Benchmark Matrix",
    description="Runs a multi-model / multi-prompt comparison matrix against a dataset and returns comparative analysis.",
)
async def create_benchmark(req: BenchmarkCreateRequest) -> BenchmarkComparisonReport:
    dataset_path = Path(req.dataset_path)
    if not dataset_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset file not found at path '{req.dataset_path}'",
        )

    model_specs = [
        ModelSpec(
            provider=m.get("provider", "mock"),
            model=m.get("model", "mock-model-v1"),
            label=m.get("label", f"{m.get('provider')}:{m.get('model')}"),
        )
        for m in req.models
    ]

    prompt_specs = [
        PromptSpec(
            name=p.get("name", "Default Prompt"),
            version=p.get("version", "v1"),
            system_prompt=p.get("system_prompt"),
        )
        for p in (req.prompts or [{"name": "Default Prompt", "version": "v1"}])
    ]

    config = BenchmarkConfig(
        dataset_path=dataset_path,
        models=model_specs,
        prompts=prompt_specs,
        concurrency=req.concurrency,
    )

    matrix_results = await BenchmarkService.run_benchmark_matrix(config)
    report = ComparisonService.analyze_and_compare(matrix_results, dataset_path)
    ComparisonService.export_reports(report, matrix_results, Path("reports"))

    return report


@router.get(
    "/{benchmark_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get Benchmark Comparison Report",
    description="Retrieves a benchmark report by ID or from reports export directory.",
)
async def get_benchmark_report(benchmark_id: str) -> Dict[str, Any]:
    report_file = Path("reports") / "benchmark_report.json"
    if not report_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark report '{benchmark_id}' not found.",
        )

    import json
    with open(report_file, "r", encoding="utf-8") as f:
        return json.load(f)
