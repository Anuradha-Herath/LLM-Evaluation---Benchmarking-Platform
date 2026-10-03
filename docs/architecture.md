# System Architecture Document

## 1. High-Level Architecture

The **LLM Evaluation & Benchmarking Platform** is architected around modular, decoupled components designed for high reproducibility, offline testing capability, and extensibility across LLM providers and metrics.

```
                                  +-----------------------+
                                  |    CLI & REST API     |
                                  |   (FastAPI / typer)   |
                                  +-----------+-----------+
                                              |
                                              v
                              +---------------+---------------+
                              |       Service Layer           |
                              | (Evaluation, Benchmark, Regr) |
                              +-------+---------------+-------+
                                      |               |
           +--------------------------+               +--------------------------+
           |                                                                     |
           v                                                                     v
+---------------------+                                               +---------------------+
|  Evaluation Engine  |                                               |  Metrics Registry   |
| (Bounded Semaphore) |                                               | (ExactMatch, Judge) |
+----------+----------+                                               +----------+----------+
           |                                                                     |
           | calls                                                               | calculates
           v                                                                     v
+---------------------+       +----------------------+                +---------------------+
| Provider Factory    | ----> | Observability Layer  |                | Data Layer          |
| (OpenAI, Groq, Det) |       | (Langfuse & NoOp)    |                | (PostgreSQL/SQLite) |
+---------------------+       +----------------------+                +---------------------+
```

---

## 2. Core Architectural Components

### 2.1 Provider Abstraction (`app/providers/`)
- **`BaseLLMProvider`**: Abstract base class enforcing contract: `generate(request: LLMRequest) -> LLMResponse` and `health_check() -> bool`.
- **Implementations**:
  - `OpenAIProvider`: Async HTTP communication with OpenAI-compatible endpoints.
  - `OllamaProvider`: Local inference via Ollama daemon.
  - `MockProvider`: Synthetic latency and fixed text for unit testing.
  - `DeterministicTestProvider`: State machine provider supporting `perfect`, `degraded`, `slow`, and `error` profiles for 100% offline, zero-quota CI/CD assertions.
- **Factory (`ProviderFactory`)**: Dynamic registration and instantiation.

### 2.2 Evaluation Engine (`app/evaluators/`)
- **`EvaluationEngine`**: Orchestrates test case iterations over datasets (`BenchmarkDataset`), manages concurrency via `asyncio.Semaphore`, captures latencies with microsecond resolution, and handles per-case errors gracefully without aborting batches.
- **`CaseRunner`**: Dispatches single prompt requests to providers, captures token usages, and computes case metrics.

### 2.3 Metrics Engine (`app/evaluators/metrics/`)
- **`MetricRegistry`**: Dynamic evaluator registry mapping task types and custom metric keys (`exact_match`, `contains`, `classification`, `similarity`, `json_validity`, `llm_judge`).
- **Standard Interface (`BaseMetricEvaluator`)**: Every metric returns a structured `MetricResult` containing `score` (0.0 to 1.0), `passed` boolean, and `details` dictionary.

### 2.4 Persistence Layer (`app/db/` & `app/repositories/`)
- **Engine**: SQLAlchemy 2.0 with PostgreSQL production backend and automatic SQLite memory fallback for lightweight offline tests.
- **Normalized Schema**:
  - `EvaluationRun`: Run metadata, configuration JSON, start/end timestamps, status.
  - `EvaluationResult`: Granular per-case outputs, latency, tokens, error state.
  - `MetricResult`: Computed scores per evaluator and case.
  - `Dataset` & `DatasetCase`: Versioned benchmark suites.
  - `Prompt`: Versioned prompt templates.

### 2.5 Observability Layer (`app/observability/`)
- **`BaseObservability`**: Standard trace, span, and score ingestion interface.
- **`LangfuseObservability`**: Native integration with Langfuse cloud/self-hosted.
- **`NoOpObservability`**: Null object pattern ensuring zero overhead when observability is disabled.

---

## 3. Data Flow

1. **Invocation**: User initiates evaluation via CLI (`python -m app evaluate`) or REST endpoint (`POST /api/v1/evaluations`).
2. **Dataset Loading**: `DatasetLoader` parses and validates JSON/CSV dataset records.
3. **Execution**: `EvaluationEngine` concurrently queries target provider using `asyncio.Semaphore`.
4. **Metrics Computation**: `MetricRegistry` executes relevant metric evaluators on each response.
5. **Observability**: `ObservabilityFactory` dispatches traces and generation spans.
6. **Persistence**: Repositories commit run, results, and metric records to PostgreSQL/SQLite.
7. **Reporting**: Summary metrics (pass rate, latency percentiles, cost) are rendered or exported to JSON/CSV.
