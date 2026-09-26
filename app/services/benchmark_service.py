import logging
from typing import Dict, List, Optional, Tuple

from app.evaluators.engine import EvaluationEngine
from app.evaluators.metrics.base import MetricResult
from app.evaluators.metrics.registry import MetricRegistry
from app.evaluators.result import EvaluationRunSummary
from app.schemas.benchmark import BenchmarkConfig, ModelSpec, PromptSpec
from app.schemas.dataset import BenchmarkDataset
from app.services.dataset_loader import DatasetLoader

logger = logging.getLogger("app.services.benchmark_service")


class BenchmarkService:
    """
    Orchestrates execution of multi-model / multi-prompt benchmark matrix experiments.
    """

    @classmethod
    async def run_benchmark_matrix(
        cls, config: BenchmarkConfig
    ) -> List[Tuple[EvaluationRunSummary, Dict[str, List[MetricResult]], ModelSpec, PromptSpec]]:
        """
        Executes a matrix of benchmark runs across all models and prompts in BenchmarkConfig.

        :param config: BenchmarkConfig spec.
        :return: List of tuples containing (run_summary, metric_results_map, model_spec, prompt_spec).
        """
        logger.info(
            f"Starting Benchmark Matrix execution: {len(config.models)} models x {len(config.prompts)} prompts against '{config.dataset_path}'"
        )

        # 1. Load dataset to get category metadata for records
        if config.dataset_path.suffix.lower() == ".csv":
            dataset: BenchmarkDataset = DatasetLoader.load_from_csv(config.dataset_path)
        else:
            dataset = DatasetLoader.load_from_json(config.dataset_path)

        record_map = {r.id: r for r in dataset.records}

        matrix_results = []

        for model_spec in config.models:
            for prompt_spec in config.prompts:
                label = model_spec.label or f"{model_spec.provider}:{model_spec.model}"
                logger.info(f"Executing experiment matrix cell: [{label}] x [Prompt: {prompt_spec.name} v{prompt_spec.version}]")

                engine = EvaluationEngine(
                    dataset_path=config.dataset_path,
                    provider_name=model_spec.provider,
                    model=model_spec.model,
                    system_prompt=prompt_spec.system_prompt,
                    config=model_spec.config,
                    concurrency=config.concurrency,
                    limit=config.limit,
                )

                summary: EvaluationRunSummary = await engine.execute()

                # 2. Compute evaluation metrics for every test case
                metric_results_map: Dict[str, List[MetricResult]] = {}
                for res in summary.results:
                    record = record_map.get(res.test_case_id)
                    category = record.category.value if record else "default"

                    metrics = MetricRegistry.get_metrics_for_category(category)
                    eval_scores: List[MetricResult] = []

                    for m in metrics:
                        score_obj = await m.evaluate(
                            response_text=res.response or "",
                            reference_answer=record.reference_answer if record else None,
                            expected_behavior=record.expected_behavior if record else None,
                            user_input=record.input if record else None,
                        )
                        eval_scores.append(score_obj)

                    metric_results_map[res.test_case_id] = eval_scores

                matrix_results.append((summary, metric_results_map, model_spec, prompt_spec))

        logger.info(f"Completed Benchmark Matrix execution ({len(matrix_results)} experiment runs total).")
        return matrix_results
