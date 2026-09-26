import asyncio
from datetime import datetime, timezone
import logging
from pathlib import Path
import uuid
from typing import Any, Dict, Optional, Union

from app.evaluators.result import EvaluationRun, EvaluationResult, EvaluationRunSummary
from app.evaluators.runner import CaseRunner
from app.providers.factory import ProviderFactory
from app.schemas.dataset import BenchmarkDataset
from app.schemas.provider import GenerationConfig
from app.services.dataset_loader import DatasetLoader

logger = logging.getLogger("app.evaluators.engine")


class EvaluationEngine:
    """
    Orchestrator responsible for running a benchmark dataset against a target LLM provider.
    Handles dataset loading, bounded concurrent execution, progress monitoring, and result aggregation.
    """

    def __init__(
        self,
        dataset_path: Union[str, Path],
        provider_name: str,
        model: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        concurrency: int = 5,
        run_id: Optional[str] = None,
        provider_kwargs: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ):
        self.dataset_path = Path(dataset_path)
        self.provider_name = provider_name
        self.model = model
        self.system_prompt = system_prompt
        self.config = config or GenerationConfig()
        self.concurrency = max(1, concurrency)
        self.run_id = run_id or f"run-{uuid.uuid4().hex[:12]}"
        self.provider_kwargs = provider_kwargs or {}
        self.limit = limit

    async def execute(self) -> EvaluationRunSummary:
        """
        Executes the full evaluation run across all records in the benchmark dataset.

        :return: EvaluationRunSummary containing run metadata, individual results, and aggregate metrics.
        """
        logger.info(
            f"Starting evaluation run '{self.run_id}' [Provider: {self.provider_name}, Model: {self.model}, Concurrency: {self.concurrency}]"
        )

        # 1. Load benchmark dataset
        if self.dataset_path.suffix.lower() == ".csv":
            dataset: BenchmarkDataset = DatasetLoader.load_from_csv(self.dataset_path)
        else:
            dataset = DatasetLoader.load_from_json(self.dataset_path)

        records_to_run = dataset.records[:self.limit] if self.limit else dataset.records

        # 2. Instantiate LLM provider
        provider = ProviderFactory.get_provider(
            self.provider_name, **self.provider_kwargs
        )

        started_at = datetime.now(timezone.utc)
        total_cases = len(records_to_run)

        from app.observability.factory import ObservabilityFactory
        obs = ObservabilityFactory.get_observability()
        obs.start_trace(
            run_id=self.run_id,
            name=f"evaluation_run:{self.model}",
            metadata={
                "dataset_version": dataset.metadata.version,
                "provider": self.provider_name,
                "model": self.model,
                "concurrency": self.concurrency,
            },
        )

        # 3. Create initial EvaluationRun object
        run_metadata = EvaluationRun(
            run_id=self.run_id,
            dataset_version=dataset.metadata.version,
            provider=self.provider_name,
            model=self.model,
            prompt_version=self.system_prompt[:30] if self.system_prompt else "default",
            configuration=self.config.model_dump(),
            started_at=started_at,
            status="running",
            total_cases=total_cases,
        )

        # 4. Bounded concurrent execution via Semaphore
        semaphore = asyncio.Semaphore(self.concurrency)

        async def worker(record):
            async with semaphore:
                return await CaseRunner.run_case(
                    run_id=self.run_id,
                    record=record,
                    provider=provider,
                    model=self.model,
                    system_prompt=self.system_prompt,
                    config=self.config,
                )

        tasks = [worker(record) for record in records_to_run]
        results = await asyncio.gather(*tasks)

        completed_at = datetime.now(timezone.utc)

        # 5. Aggregate results and statistics
        passed_cases = sum(1 for r in results if r.error is None)
        failed_cases = sum(1 for r in results if r.error is not None)

        run_metadata.completed_at = completed_at
        run_metadata.status = "completed" if failed_cases == 0 else ("partial_failure" if passed_cases > 0 else "failed")
        run_metadata.passed_cases = passed_cases
        run_metadata.failed_cases = failed_cases

        latencies = [r.latency_ms for r in results if r.error is None]
        avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

        total_input_tokens = sum(r.input_tokens or 0 for r in results)
        total_output_tokens = sum(r.output_tokens or 0 for r in results)
        total_tokens = sum(r.total_tokens or (r.input_tokens or 0) + (r.output_tokens or 0) for r in results)

        logger.info(
            f"Completed run '{self.run_id}': {passed_cases}/{total_cases} passed ({failed_cases} failed) in {(completed_at - started_at).total_seconds():.2f}s"
        )

        obs.end_trace(run_id=self.run_id, status=run_metadata.status)
        obs.flush()

        return EvaluationRunSummary(
            run=run_metadata,
            results=results,
            avg_latency_ms=avg_latency,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_tokens=total_tokens,
        )
