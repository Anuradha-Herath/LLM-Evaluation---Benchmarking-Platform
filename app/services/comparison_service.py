import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from app.core.pricing import calculate_estimated_cost
from app.evaluators.metrics.base import MetricResult
from app.evaluators.result import EvaluationRunSummary
from app.schemas.benchmark import (
    BenchmarkComparisonReport,
    FailureCaseAnalysis,
    ModelSpec,
    PromptSpec,
    RunComparisonStats,
)
from app.schemas.dataset import BenchmarkDataset
from app.services.dataset_loader import DatasetLoader

logger = logging.getLogger("app.services.comparison_service")


class ComparisonService:
    """
    Data analysis and report generation service using pandas to compare benchmark runs.
    """

    @classmethod
    def analyze_and_compare(
        cls,
        matrix_results: List[Tuple[EvaluationRunSummary, Dict[str, List[MetricResult]], ModelSpec, PromptSpec]],
        dataset_path: Path,
    ) -> BenchmarkComparisonReport:
        """
        Processes benchmark run results using pandas and computes comparative statistics.
        """
        # Load dataset to get case category and expected_behavior mapping
        if dataset_path.suffix.lower() == ".csv":
            dataset: BenchmarkDataset = DatasetLoader.load_from_csv(dataset_path)
        else:
            dataset = DatasetLoader.load_from_json(dataset_path)

        record_map = {r.id: r for r in dataset.records}

        summary_runs: List[RunComparisonStats] = []
        failure_cases: List[FailureCaseAnalysis] = []

        for summary, metric_map, model_spec, prompt_spec in matrix_results:
            run_data = summary.run
            label = model_spec.label or f"{model_spec.provider}:{model_spec.model}"

            # 1. Build pandas DataFrame for run results
            rows = []
            for res in summary.results:
                rec = record_map.get(res.test_case_id)
                category = rec.category.value if rec else "unknown"
                expected_beh = rec.expected_behavior if rec else "N/A"

                m_list = metric_map.get(res.test_case_id, [])
                avg_metric_score = (
                    sum(m.score for m in m_list) / len(m_list) if m_list else 0.0
                )
                passed_case = res.error is None and avg_metric_score >= 0.5

                rows.append({
                    "case_id": res.test_case_id,
                    "category": category,
                    "expected_behavior": expected_beh,
                    "response": res.response,
                    "latency_ms": res.latency_ms,
                    "input_tokens": res.input_tokens or 0,
                    "output_tokens": res.output_tokens or 0,
                    "total_tokens": res.total_tokens or (res.input_tokens or 0) + (res.output_tokens or 0),
                    "error": res.error,
                    "avg_metric_score": round(avg_metric_score, 4),
                    "passed": passed_case,
                })

                # Check if case failed for Failure Analysis
                if not passed_case:
                    failure_cases.append(
                        FailureCaseAnalysis(
                            case_id=res.test_case_id,
                            category=category,
                            provider=model_spec.provider,
                            model=model_spec.model,
                            prompt_version=prompt_spec.version,
                            expected_behavior=expected_beh,
                            actual_response=res.response,
                            metric_results={m.metric_name: m.score for m in m_list},
                            error_message=res.error or "Metric score below passing threshold (0.5).",
                        )
                    )

            df = pd.DataFrame(rows)

            # 2. Compute pandas aggregations
            total_cases = len(df)
            passed_cases = int(df["passed"].sum())
            failed_cases = total_cases - passed_cases
            pass_rate_pct = round((passed_cases / total_cases) * 100.0, 2) if total_cases > 0 else 0.0

            avg_latency = round(df["latency_ms"].mean(), 2) if total_cases > 0 else 0.0
            median_latency = round(df["latency_ms"].median(), 2) if total_cases > 0 else 0.0

            total_in_tokens = int(df["input_tokens"].sum())
            total_out_tokens = int(df["output_tokens"].sum())
            total_tokens = int(df["total_tokens"].sum())

            # 3. Calculate estimated cost
            est_cost = calculate_estimated_cost(model_spec.model, total_in_tokens, total_out_tokens)

            # 4. Compute per-category average metric score
            cat_scores = {}
            if "category" in df.columns and total_cases > 0:
                cat_grp = df.groupby("category")["avg_metric_score"].mean()
                cat_scores = {str(cat): round(float(val), 4) for cat, val in cat_grp.items()}

            summary_runs.append(
                RunComparisonStats(
                    run_id=run_data.run_id,
                    label=label,
                    provider=model_spec.provider,
                    model=model_spec.model,
                    prompt_version=prompt_spec.version,
                    total_cases=total_cases,
                    passed_cases=passed_cases,
                    failed_cases=failed_cases,
                    pass_rate_pct=pass_rate_pct,
                    avg_latency_ms=avg_latency,
                    median_latency_ms=median_latency,
                    total_input_tokens=total_in_tokens,
                    total_output_tokens=total_out_tokens,
                    total_tokens=total_tokens,
                    estimated_cost_usd=est_cost,
                    category_scores=cat_scores,
                )
            )

        return BenchmarkComparisonReport(
            benchmark_name="LLM Evaluation Comparison Report",
            dataset_version=dataset.metadata.version,
            total_experiments=len(summary_runs),
            summary_runs=summary_runs,
            failure_cases=failure_cases,
        )

    @classmethod
    def export_reports(
        cls,
        report: BenchmarkComparisonReport,
        matrix_results: List[Tuple[EvaluationRunSummary, Dict[str, List[MetricResult]], ModelSpec, PromptSpec]],
        output_dir: Path,
    ) -> Dict[str, Path]:
        """
        Exports benchmark results to benchmark_results.csv, benchmark_summary.csv, and benchmark_report.json.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        results_csv_path = output_dir / "benchmark_results.csv"
        summary_csv_path = output_dir / "benchmark_summary.csv"
        report_json_path = output_dir / "benchmark_report.json"

        # 1. Generate itemized benchmark_results.csv
        all_rows = []
        for summary, metric_map, model_spec, prompt_spec in matrix_results:
            for res in summary.results:
                m_list = metric_map.get(res.test_case_id, [])
                scores_str = "; ".join([f"{m.metric_name}={m.score}" for m in m_list])
                all_rows.append({
                    "run_id": summary.run.run_id,
                    "provider": model_spec.provider,
                    "model": model_spec.model,
                    "prompt_version": prompt_spec.version,
                    "test_case_id": res.test_case_id,
                    "response": res.response,
                    "latency_ms": res.latency_ms,
                    "input_tokens": res.input_tokens,
                    "output_tokens": res.output_tokens,
                    "total_tokens": res.total_tokens,
                    "error": res.error,
                    "metric_scores": scores_str,
                })

        df_results = pd.DataFrame(all_rows)
        df_results.to_csv(results_csv_path, index=False)

        # 2. Generate benchmark_summary.csv
        summary_rows = [r.model_dump() for r in report.summary_runs]
        df_summary = pd.DataFrame(summary_rows)
        df_summary.to_csv(summary_csv_path, index=False)

        # 3. Generate benchmark_report.json
        with open(report_json_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(mode="json"), f, indent=2)

        logger.info(f"Exported benchmark reports to '{output_dir}'")
        return {
            "results_csv": results_csv_path,
            "summary_csv": summary_csv_path,
            "report_json": report_json_path,
        }
