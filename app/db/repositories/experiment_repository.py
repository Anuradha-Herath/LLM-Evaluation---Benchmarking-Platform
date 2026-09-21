from typing import List, Optional, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from app.evaluators.metrics.base import MetricResult
from app.evaluators.result import EvaluationRunSummary
from app.models.evaluation import EvaluationResultDB, EvaluationRunDB, MetricResultDB


class ExperimentRepository:
    """
    Repository for persisting and querying evaluation runs, case results, and metrics.
    """

    def __init__(self, session: Union[AsyncSession, Session]):
        self.session = session

    def save_evaluation_run_sync(
        self,
        summary: EvaluationRunSummary,
        metric_results_map: Optional[dict] = None,
    ) -> EvaluationRunDB:
        """
        Synchronous saving of an EvaluationRunSummary into the database.
        """
        run_data = summary.run

        run_db = EvaluationRunDB(
            run_id=run_data.run_id,
            dataset_version=run_data.dataset_version,
            provider=run_data.provider,
            model=run_data.model,
            prompt_version=run_data.prompt_version,
            configuration=run_data.configuration,
            status=run_data.status,
            total_cases=run_data.total_cases,
            passed_cases=run_data.passed_cases,
            failed_cases=run_data.failed_cases,
            started_at=run_data.started_at,
            completed_at=run_data.completed_at,
        )
        self.session.add(run_db)
        self.session.flush()

        for res in summary.results:
            res_db = EvaluationResultDB(
                run_id=run_db.id,
                case_id=res.test_case_id,
                response_text=res.response,
                latency_ms=res.latency_ms,
                input_tokens=res.input_tokens,
                output_tokens=res.output_tokens,
                total_tokens=res.total_tokens,
                error=res.error,
                timestamp=res.timestamp,
            )
            self.session.add(res_db)
            self.session.flush()

            if metric_results_map and res.test_case_id in metric_results_map:
                for m_res in metric_results_map[res.test_case_id]:
                    if isinstance(m_res, MetricResult):
                        metric_db = MetricResultDB(
                            result_id=res_db.id,
                            metric_name=m_res.metric_name,
                            metric_version=m_res.metric_version,
                            score=m_res.score,
                            passed=m_res.passed,
                            reasoning=m_res.reasoning,
                            judge_model=m_res.judge_model,
                            metadata_json=m_res.metadata,
                        )
                        self.session.add(metric_db)

        self.session.commit()
        return run_db

    async def save_evaluation_run(
        self,
        summary: EvaluationRunSummary,
        metric_results_map: Optional[dict] = None,
    ) -> EvaluationRunDB:
        """
        Asynchronous wrapper for saving an EvaluationRunSummary.
        """
        return self.save_evaluation_run_sync(summary, metric_results_map=metric_results_map)

    def get_run_by_id_sync(self, run_id: str) -> Optional[EvaluationRunDB]:
        stmt = (
            select(EvaluationRunDB)
            .options(
                selectinload(EvaluationRunDB.results).selectinload(
                    EvaluationResultDB.metric_results
                )
            )
            .where(EvaluationRunDB.run_id == run_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    async def get_run_by_id(self, run_id: str) -> Optional[EvaluationRunDB]:
        return self.get_run_by_id_sync(run_id)

    def get_run_results_sync(self, run_id: str) -> List[EvaluationResultDB]:
        stmt = (
            select(EvaluationResultDB)
            .join(EvaluationRunDB, EvaluationRunDB.id == EvaluationResultDB.run_id)
            .options(selectinload(EvaluationResultDB.metric_results))
            .where(EvaluationRunDB.run_id == run_id)
        )
        return list(self.session.execute(stmt).scalars().all())

    async def get_run_results(self, run_id: str) -> List[EvaluationResultDB]:
        return self.get_run_results_sync(run_id)

    def get_metrics_for_result_sync(self, result_db_id: str) -> List[MetricResultDB]:
        stmt = select(MetricResultDB).where(MetricResultDB.result_id == result_db_id)
        return list(self.session.execute(stmt).scalars().all())

    async def get_metrics_for_result(self, result_db_id: str) -> List[MetricResultDB]:
        return self.get_metrics_for_result_sync(result_db_id)
