import argparse
import asyncio
import json
import logging
from pathlib import Path
import sys

# Ensure root directory is on PYTHONPATH
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.evaluators.engine import EvaluationEngine
from app.schemas.provider import GenerationConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="LLM Evaluation & Benchmarking Platform CLI Tool",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: evaluate
    eval_parser = subparsers.add_parser(
        "evaluate", help="Run a benchmark dataset against a specified LLM provider."
    )
    eval_parser.add_argument(
        "--dataset",
        type=str,
        default="datasets/benchmark_v1.json",
        help="Path to evaluation dataset file (.json or .csv). Default: datasets/benchmark_v1.json",
    )
    eval_parser.add_argument(
        "--provider",
        type=str,
        default="mock",
        choices=["openai", "ollama", "mock"],
        help="LLM Provider to use ('mock', 'openai', 'ollama'). Default: mock",
    )
    eval_parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Target model identifier (defaults: mock-model for mock, gpt-4o-mini for openai, llama3 for ollama)",
    )
    eval_parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Optional system prompt or instructions template",
    )
    eval_parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (0.0 to 2.0). Default: 0.7",
    )
    eval_parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Maximum concurrent request workers. Default: 5",
    )
    eval_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to save full JSON report (e.g. reports/run_results.json)",
    )

    return parser


async def main_async() -> None:
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "evaluate":
        model = args.model
        if not model:
            if args.provider == "openai":
                model = "gpt-4o-mini"
            elif args.provider == "ollama":
                model = "llama3"
            else:
                model = "mock-model-v1"

        dataset_path = Path(args.dataset)

        print("\n" + "=" * 60)
        print("  LLM EVALUATION & BENCHMARKING ENGINE")
        print("=" * 60)
        print(f" Dataset Path:  {dataset_path}")
        print(f" Provider:      {args.provider.upper()}")
        print(f" Target Model:  {model}")
        print(f" Concurrency:   {args.concurrency}")
        print(f" Temperature:   {args.temperature}")
        if args.prompt:
            print(f" System Prompt: '{args.prompt}'")
        print("=" * 60 + "\n")

        engine = EvaluationEngine(
            dataset_path=dataset_path,
            provider_name=args.provider,
            model=model,
            system_prompt=args.prompt,
            config=GenerationConfig(temperature=args.temperature),
            concurrency=args.concurrency,
        )

        summary = await engine.execute()

        print("\n" + "-" * 60)
        print("  EVALUATION SUMMARY REPORT")
        print("-" * 60)
        print(f" Run ID:          {summary.run.run_id}")
        print(f" Dataset Version: {summary.run.dataset_version}")
        print(f" Status:          {summary.run.status.upper()}")
        print(f" Total Cases:     {summary.run.total_cases}")
        print(f" Passed Cases:    {summary.run.passed_cases}")
        print(f" Failed Cases:    {summary.run.failed_cases}")
        print(f" Avg Latency:     {summary.avg_latency_ms} ms")
        print(f" Total Tokens:    {summary.total_tokens} (In: {summary.total_input_tokens}, Out: {summary.total_output_tokens})")
        print("-" * 60 + "\n")

        # Save JSON output report if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(summary.model_dump(mode="json"), f, indent=2)
            print(f"[SUCCESS] Full summary report saved to: {output_path}\n")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
