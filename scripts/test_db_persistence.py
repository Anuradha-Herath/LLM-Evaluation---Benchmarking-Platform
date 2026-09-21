import asyncio
import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.db.repositories.experiment_repository import ExperimentRepository
from app.db.session import SyncSessionLocal
from app.evaluators.engine import EvaluationEngine
from app.evaluators.metrics.registry import MetricRegistry
from app.schemas.dataset import DatasetCategory


async def run_and_persist_demo():
    print("\n==================================================")
    print(" Running Evaluation Engine & Persisting to Database")
    print("==================================================\n")

    dataset_path = root_dir / "datasets" / "benchmark_v1.json"

    engine = EvaluationEngine(
        dataset_path=dataset_path,
        provider_name="mock",
        model="mock-gpt4",
        concurrency=10,
    )

    # 1. Execute Evaluation Run
    summary = await engine.execute()
    print(f"[1/3] Evaluation Run '{summary.run.run_id}' completed. ({summary.run.passed_cases}/{summary.run.total_cases} passed)")

    # 2. Evaluate sample metrics for each result
    metric_results_map = {}
    for res in summary.results:
        # Evaluate default category metrics
        metrics = MetricRegistry.get_metrics_for_category("factual question")
        eval_scores = []
        for m in metrics:
            score_obj = await m.evaluate(
                response_text=res.response or "",
                reference_answer="ISO 20022 is a financial messaging standard",
            )
            eval_scores.append(score_obj)
        metric_results_map[res.test_case_id] = eval_scores

    # 3. Persist into Database
    with SyncSessionLocal() as session:
        repo = ExperimentRepository(session)
        db_run = repo.save_evaluation_run_sync(summary, metric_results_map=metric_results_map)
        print(f"[2/3] Successfully persisted run '{db_run.run_id}' into Database (ID: {db_run.id}).")

        # 4. Retrieve Run and Metrics from Database
        retrieved_run = repo.get_run_by_id_sync(summary.run.run_id)
        results = repo.get_run_results_sync(summary.run.run_id)

        print("\n---------------- PERSISTED DATABASE RETRIEVAL ----------------")
        print(f"Run ID:            {retrieved_run.run_id}")
        print(f"Provider:          {retrieved_run.provider}")
        print(f"Model:             {retrieved_run.model}")
        print(f"Status:            {retrieved_run.status}")
        print(f"Total Cases:       {retrieved_run.total_cases}")
        print(f"Persisted Results: {len(results)}")
        
        sample_res = results[0]
        metrics_list = repo.get_metrics_for_result_sync(sample_res.id)
        print(f"Sample Case ID:    {sample_res.case_id}")
        print(f"Response:          {sample_res.response_text[:50]}...")
        print(f"Associated Metrics:{len(metrics_list)}")
        for m in metrics_list:
            print(f"  - Metric: {m.metric_name} | Score: {m.score} | Passed: {m.passed}")
        print("--------------------------------------------------------------\n")


if __name__ == "__main__":
    asyncio.run(run_and_persist_demo())
