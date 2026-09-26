import pytest
from pathlib import Path

from app.core.pricing import calculate_estimated_cost
from app.schemas.benchmark import BenchmarkConfig, ModelSpec, PromptSpec
from app.services.benchmark_service import BenchmarkService
from app.services.comparison_service import ComparisonService


def test_pricing_calculation():
    """Test cost estimation calculation across known models."""
    # 1M input ($0.15) + 1M output ($0.60) for gpt-4o-mini = $0.75
    cost = calculate_estimated_cost("gpt-4o-mini", 1_000_000, 1_000_000)
    assert cost == 0.75

    # Mock model free cost
    free_cost = calculate_estimated_cost("mock-model-v1", 10_000, 10_000)
    assert free_cost == 0.0


@pytest.mark.asyncio
async def test_benchmark_matrix_and_comparison(tmp_path: Path):
    """Test multi-model benchmark matrix execution, pandas comparison, and file exports."""
    # Create small 3-case benchmark file
    import json
    dataset_file = tmp_path / "test_bench.json"
    dataset_data = {
        "metadata": {"version": "v1", "name": "Bench Test", "description": "Test", "total_records": 3},
        "records": [
            {
                "id": "CASE-001",
                "category": "factual question",
                "input": "Q1",
                "expected_behavior": "B1",
            },
            {
                "id": "CASE-002",
                "category": "classification",
                "input": "Q2",
                "expected_behavior": "B2",
            },
            {
                "id": "CASE-003",
                "category": "summarization",
                "input": "Q3",
                "expected_behavior": "B3",
            },
        ],
    }
    with open(dataset_file, "w", encoding="utf-8") as f:
        json.dump(dataset_data, f)

    # Configure 2 models matrix: Model A vs Model B
    models = [
        ModelSpec(provider="mock", model="mock-model-v1", label="Model A (V1)"),
        ModelSpec(provider="mock", model="mock-model-v2", label="Model B (V2)"),
    ]
    prompts = [PromptSpec(name="Default Prompt", version="v1", system_prompt=None)]

    config = BenchmarkConfig(
        dataset_path=dataset_file,
        models=models,
        prompts=prompts,
        concurrency=2,
    )

    # 1. Run Matrix Execution
    matrix_results = await BenchmarkService.run_benchmark_matrix(config)
    assert len(matrix_results) == 2

    # 2. Analyze & Compare via ComparisonService (pandas)
    report = ComparisonService.analyze_and_compare(matrix_results, dataset_file)
    assert report.total_experiments == 2
    assert len(report.summary_runs) == 2
    assert report.summary_runs[0].label == "Model A (V1)"
    assert report.summary_runs[1].label == "Model B (V2)"

    # 3. Export Reports
    export_dir = tmp_path / "reports"
    exports = ComparisonService.export_reports(report, matrix_results, export_dir)

    assert exports["results_csv"].exists()
    assert exports["summary_csv"].exists()
    assert exports["report_json"].exists()

    # Read exported summary CSV using pandas
    import pandas as pd
    df_summary = pd.read_csv(exports["summary_csv"])
    assert len(df_summary) == 2
    assert "pass_rate_pct" in df_summary.columns
    assert "avg_latency_ms" in df_summary.columns
    assert "median_latency_ms" in df_summary.columns
    assert "estimated_cost_usd" in df_summary.columns
