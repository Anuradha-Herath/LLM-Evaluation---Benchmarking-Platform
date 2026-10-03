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
        help="LLM Provider to use ('mock', 'openai', 'ollama', 'deterministic', etc.). Default: mock",
    )
    eval_parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Target model identifier (defaults: mock-model for mock, gpt-4o-mini for openai, llama3 for ollama, perfect for deterministic)",
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
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of test cases to evaluate.",
    )
    eval_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to save full JSON report (e.g. reports/run_results.json)",
    )

    # Subcommand: benchmark
    bench_parser = subparsers.add_parser(
        "benchmark", help="Run a multi-model benchmark comparison matrix against a dataset."
    )
    bench_parser.add_argument(
        "--dataset",
        type=str,
        default="datasets/benchmark_v1.json",
        help="Path to evaluation dataset file (.json or .csv). Default: datasets/benchmark_v1.json",
    )
    bench_parser.add_argument(
        "--models",
        type=str,
        default="mock:mock-model-v1,mock:mock-model-v2",
        help="Comma-separated provider:model specs (e.g. 'mock:mock-model-v1,mock:mock-model-v2'). Default: mock:mock-model-v1,mock:mock-model-v2",
    )
    bench_parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Maximum concurrent request workers per experiment. Default: 5",
    )
    bench_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of test cases to evaluate.",
    )
    bench_parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Directory to save benchmark_results.csv, benchmark_summary.csv, and benchmark_report.json. Default: reports",
    )

    # Subcommand: regression
    reg_parser = subparsers.add_parser(
        "regression", help="Run automated LLM regression test comparing Candidate against Baseline."
    )
    reg_parser.add_argument(
        "--dataset",
        type=str,
        default="datasets/benchmark_v1.json",
        help="Path to evaluation dataset file (.json or .csv). Default: datasets/benchmark_v1.json",
    )
    reg_parser.add_argument(
        "--baseline-model",
        type=str,
        default="mock:mock-model-v1",
        help="Baseline provider:model spec or model name. Default: mock:mock-model-v1",
    )
    reg_parser.add_argument(
        "--baseline-provider",
        type=str,
        default=None,
        help="Optional baseline provider override.",
    )
    reg_parser.add_argument(
        "--candidate-model",
        type=str,
        default="mock:mock-model-v1",
        help="Candidate provider:model spec or model name. Default: mock:mock-model-v1",
    )
    reg_parser.add_argument(
        "--candidate-provider",
        type=str,
        default=None,
        help="Optional candidate provider override.",
    )
    reg_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of test cases to evaluate.",
    )
    reg_parser.add_argument(
        "--config-file",
        type=str,
        default=None,
        help="Optional path to regression thresholds JSON configuration file.",
    )
    reg_parser.add_argument(
        "--min-pass-rate",
        type=float,
        default=None,
        help="Override minimum pass rate percentage (0-100).",
    )
    reg_parser.add_argument(
        "--threshold-accuracy",
        type=float,
        default=None,
        help="Override minimum accuracy threshold (0.0 - 1.0).",
    )
    reg_parser.add_argument(
        "--threshold-failure-rate",
        type=float,
        default=None,
        help="Override maximum allowed failure rate (0.0 - 1.0).",
    )
    reg_parser.add_argument(
        "--max-avg-latency",
        type=float,
        default=None,
        help="Override maximum allowed average latency in ms.",
    )
    reg_parser.add_argument(
        "--max-pass-rate-drop",
        type=float,
        default=None,
        help="Override maximum allowed pass rate drop percentage.",
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
            elif args.provider == "groq":
                model = "llama-3.3-70b-versatile"
            elif args.provider == "gemini":
                model = "gemini-3.8-flash"
            elif args.provider == "ollama":
                model = "llama3"
            elif args.provider == "deterministic":
                model = "perfect"
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
        if args.limit:
            print(f" Case Limit:    {args.limit}")
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
            limit=args.limit,
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

    elif args.command == "benchmark":
        from app.schemas.benchmark import BenchmarkConfig, ModelSpec, PromptSpec
        from app.services.benchmark_service import BenchmarkService
        from app.services.comparison_service import ComparisonService

        dataset_path = Path(args.dataset)
        output_dir = Path(args.output_dir)

        # Parse models argument (e.g. "mock:mock-model-v1,mock:mock-model-v2")
        model_specs = []
        for item in args.models.split(","):
            parts = item.strip().split(":")
            prov = parts[0]
            mod = parts[1] if len(parts) > 1 else prov
            model_specs.append(ModelSpec(provider=prov, model=mod, label=f"{prov}:{mod}"))

        prompt_spec = PromptSpec(name="Default Prompt", version="v1", system_prompt=None)

        bench_config = BenchmarkConfig(
            dataset_path=dataset_path,
            models=model_specs,
            prompts=[prompt_spec],
            concurrency=args.concurrency,
            limit=args.limit,
        )

        print("\n" + "=" * 65)
        print("  LLM BENCHMARK MATRIX & EXPERIMENT COMPARISON ENGINE")
        print("=" * 65)
        print(f" Dataset Path:  {dataset_path}")
        print(f" Target Models: {[m.label for m in model_specs]}")
        print(f" Concurrency:   {args.concurrency}")
        if args.limit:
            print(f" Case Limit:    {args.limit}")
        print("=" * 65 + "\n")

        matrix_results = await BenchmarkService.run_benchmark_matrix(bench_config)
        report = ComparisonService.analyze_and_compare(matrix_results, dataset_path)
        exports = ComparisonService.export_reports(report, matrix_results, output_dir)

        print("\n" + "-" * 65)
        print("  BENCHMARK COMPARISON SUMMARY TABLE")
        print("-" * 65)
        print(f"{'Model/Label':<22} | {'Pass Rate':<10} | {'Avg Latency':<12} | {'Med Latency':<12} | {'Est. Cost':<10}")
        print("-" * 65)
        for s in report.summary_runs:
            print(f"{s.label:<22} | {s.pass_rate_pct:>8.1f}% | {s.avg_latency_ms:>9.1f} ms | {s.median_latency_ms:>9.1f} ms | ${s.estimated_cost_usd:>8.4f}")
        print("-" * 65 + "\n")

        print(f"[SUCCESS] Exported reports to '{output_dir}':")
        print(f"  - {exports['results_csv']}")
        print(f"  - {exports['summary_csv']}")
        print(f"  - {exports['report_json']}\n")

    elif args.command == "regression":
        from app.schemas.benchmark import BenchmarkConfig, ModelSpec, PromptSpec
        from app.schemas.regression import RegressionConfig
        from app.services.benchmark_service import BenchmarkService
        from app.services.regression_service import RegressionService

        dataset_path = Path(args.dataset)

        # Load regression config file if provided
        reg_config = RegressionConfig()
        if args.config_file:
            cfg_file = Path(args.config_file)
            if cfg_file.is_file():
                with open(cfg_file, "r", encoding="utf-8") as f:
                    reg_config = RegressionConfig.model_validate(json.load(f))

        # Apply CLI overrides
        if args.min_pass_rate is not None:
            reg_config.min_pass_rate_pct = args.min_pass_rate
        if args.threshold_accuracy is not None:
            reg_config.min_pass_rate_pct = args.threshold_accuracy * 100.0 if args.threshold_accuracy <= 1.0 else args.threshold_accuracy
            reg_config.min_avg_metric_score = args.threshold_accuracy if args.threshold_accuracy <= 1.0 else args.threshold_accuracy / 100.0
        if args.threshold_failure_rate is not None:
            reg_config.max_failure_rate_pct = args.threshold_failure_rate * 100.0 if args.threshold_failure_rate <= 1.0 else args.threshold_failure_rate
        if args.max_avg_latency is not None:
            reg_config.max_avg_latency_ms = args.max_avg_latency
        if args.max_pass_rate_drop is not None:
            reg_config.max_allowed_pass_rate_drop_pct = args.max_pass_rate_drop

        # Parse baseline & candidate specs
        base_raw = args.baseline_model
        if args.baseline_provider:
            base_prov = args.baseline_provider
            base_mod = base_raw.split(":")[1] if ":" in base_raw else base_raw
        elif ":" in base_raw:
            parts = base_raw.split(":", 1)
            base_prov, base_mod = parts[0], parts[1]
        else:
            base_prov, base_mod = "mock", base_raw
        base_spec = ModelSpec(provider=base_prov, model=base_mod, label=f"Baseline ({base_prov}:{base_mod})")

        cand_raw = args.candidate_model
        if args.candidate_provider:
            cand_prov = args.candidate_provider
            cand_mod = cand_raw.split(":")[1] if ":" in cand_raw else cand_raw
        elif ":" in cand_raw:
            parts = cand_raw.split(":", 1)
            cand_prov, cand_mod = parts[0], parts[1]
        else:
            cand_prov, cand_mod = "mock", cand_raw
        cand_spec = ModelSpec(provider=cand_prov, model=cand_mod, label=f"Candidate ({cand_prov}:{cand_mod})")

        prompt_spec = PromptSpec(name="Default Prompt", version="v1", system_prompt=None)

        print("\n" + "=" * 70)
        print("  AUTOMATED LLM REGRESSION TESTING SUITE")
        print("=" * 70)
        print(f" Dataset Path:     {dataset_path}")
        print(f" Baseline Model:   {base_spec.label}")
        print(f" Candidate Model:  {cand_spec.label}")
        print(f" Min Pass Rate:    {reg_config.min_pass_rate_pct}%")
        print(f" Max Failure Rate: {reg_config.max_failure_rate_pct}%")
        print(f" Max Latency:      {reg_config.max_avg_latency_ms} ms")
        if args.limit:
            print(f" Case Limit:       {args.limit}")
        print("=" * 70 + "\n")

        # Execute Baseline & Candidate Benchmark Runs
        bench_config = BenchmarkConfig(
            dataset_path=dataset_path,
            models=[base_spec, cand_spec],
            prompts=[prompt_spec],
            concurrency=5,
            limit=args.limit,
        )
        matrix_results = await BenchmarkService.run_benchmark_matrix(bench_config)

        base_summary, base_metric_map, _, _ = matrix_results[0]
        cand_summary, cand_metric_map, _, _ = matrix_results[1]

        report = RegressionService.evaluate_regression(
            baseline_summary=base_summary,
            candidate_summary=cand_summary,
            baseline_metric_map=base_metric_map,
            candidate_metric_map=cand_metric_map,
            config=reg_config,
            baseline_label=base_spec.label,
            candidate_label=cand_spec.label,
        )

        print("\n" + "-" * 70)
        print(f"  REGRESSION TEST STATUS: {report.status}")
        print("-" * 70)
        print(f" Summary: {report.summary}\n")

        if report.violations:
            print("VIOLATIONS BREAKDOWN:")
            print(f"{'Metric':<22} | {'Baseline':<10} | {'Candidate':<10} | {'Abs Diff':<10} | {'Pct Diff':<10}")
            print("-" * 70)
            for v in report.violations:
                print(f"{v.metric_name:<22} | {v.baseline_value:>10.2f} | {v.candidate_value:>10.2f} | {v.abs_diff:>+10.2f} | {v.pct_diff:>+9.2f}%")
                print(f"  -> Threshold Rule: {v.threshold_rule}")
                if v.affected_cases:
                    print(f"  -> Affected Test Cases ({len(v.affected_cases)}): {v.affected_cases[:5]}")
            print("-" * 70 + "\n")

        if report.status == "FAIL":
            print("[FAIL] REGRESSION DETECTED! Exiting with non-zero exit code (1) for CI/CD gating.\n")
            sys.exit(1)
        else:
            print("[PASS] NO REGRESSION DETECTED! Exit code (0).\n")



def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
