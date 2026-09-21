import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.evaluators.metrics.registry import MetricRegistry
from app.evaluators.metrics.llm_judge import LLMJudgeMetric
from app.providers.mock_provider import MockProvider
from app.services.dataset_loader import DatasetLoader


async def run_metrics_demo() -> None:
    print("\n==================================================")
    print(" Running Evaluation Metrics Against Sample Cases")
    print("==================================================\n")

    dataset_path = root_dir / "datasets" / "benchmark_v1.json"
    dataset = DatasetLoader.load_from_json(dataset_path)

    # Select 4 representative cases
    sample_cases = [
        ("FACT-002", "A SOC 2 Type 1 report assesses security design at a point in time, while Type 2 evaluates operating effectiveness over a period."),
        ("CLAS-002", "CRITICAL"),
        ("EXTR-001", '{"invoice_id": "INV-2026-889", "amount": 4500.0, "currency": "USD", "due_date": "2026-11-15"}'),
        ("INST-001", "Experience Pure Silence With Crystal Clear Audio"),
    ]

    record_map = {r.id: r for r in dataset.records}

    # Mock Judge for open-ended LLM-as-a-judge demo
    mock_judge = MockProvider(
        mock_text='{"score": 0.95, "reasoning": "Accurate, concise, and meets all criteria.", "passed": true}'
    )
    llm_judge = LLMJudgeMetric(judge_provider=mock_judge, judge_model="gpt-4o-judge")

    for case_id, candidate_response in sample_cases:
        record = record_map[case_id]
        print(f"--------------------------------------------------")
        print(f"CASE ID:            {record.id}")
        print(f"Category:           {record.category.value}")
        print(f"Input Prompt:       {record.input[:60]}...")
        print(f"Candidate Response: {candidate_response[:60]}...")
        print(f"Reference Answer:   {(record.reference_answer or 'N/A')[:60]}...")
        print(f"--------------------------------------------------")
        print("METRIC EVALUATION RESULTS:")

        metrics = MetricRegistry.get_metrics_for_category(record.category.value)
        # Add LLM Judge metric as well
        all_metrics = metrics + [llm_judge]

        for metric in all_metrics:
            result = await metric.evaluate(
                response_text=candidate_response,
                reference_answer=record.reference_answer,
                expected_behavior=record.expected_behavior,
                user_input=record.input,
            )

            print(f"  * {result.metric_name} (v{result.metric_version}):")
            print(f"      Score:       {result.score:.2f}")
            print(f"      Passed:      {result.passed}")
            print(f"      Reasoning:   {result.reasoning}")
            if result.judge_model:
                print(f"      Judge Model: {result.judge_model}")
            print(f"      Metadata:    {json.dumps(result.metadata)}")
        print()


if __name__ == "__main__":
    asyncio.run(run_metrics_demo())
