# LLM Evaluation & Benchmarking Platform

An enterprise-grade, reproducible evaluation and regression testing framework for systematically benchmarking Large Language Models (LLMs), prompt variants, and inference configurations across standardized task distributions.

---

## Problem

Evaluating production LLM applications is notoriously challenging compared to deterministic software:

1. **Non-Deterministic Outputs & Stochastic Drift**: LLM outputs vary across runs, versions, and prompt alterations. Subtle edits in prompt phrasing or model weights can cause catastrophic regressions in structured formatting or domain reasoning.
2. **The "Vibes-Based" Evaluation Trap**: Engineering teams frequently assess model quality by eyeballing a few prompt outputs in a playground, leading to confirmation bias and undetected production regressions.
3. **Flaky & Expensive CI/CD**: Running automated tests against paid LLM APIs on every commit consumes rate limits, runs up huge cloud bills, and breaks builds due to upstream network flakiness.
4. **Metric Myopia**: Relying solely on single metrics (e.g. exact match or semantic similarity) fails because different tasks demand different evaluation strategies (e.g., JSON schema adherence vs. classification accuracy vs. conversational tone).
5. **Lack of Reproducibility**: Missing records of system prompts, inference parameters (temperature, top_p), model snapshots, and dataset versions make historical comparison nearly impossible.

---

## Solution

The **LLM Evaluation & Benchmarking Platform** solves these challenges by providing:

- **Isolated & Reproducible Benchmark Engine**: Bounded concurrent execution over versioned datasets with microsecond latency recording, token telemetry, and non-blocking error isolation.
- **Multimodal Evaluation Framework**: Rule-based metrics (Exact Match, Contains, Classification Precision/Recall/F1, JSON Validity, Response Length) combined with structured LLM-as-a-Judge evaluators.
- **Automated Regression Quality Gates**: CLI-driven quality threshold assertions (`accuracy >= 0.80`, `latency_increase <= 20%`) with non-zero exit codes for CI/CD gating.
- **Zero-Quota Deterministic CI Testing**: Offline `DeterministicTestProvider` enabling full unit, integration, database, metric, and regression pipeline execution in GitHub Actions with 0 external API cost.
- **Normalized PostgreSQL & Experiment Storage**: Immutably records every run configuration, per-case result, latency percentile, token usage, and metric score.
- **Full-Stack Dashboard & REST API**: Production FastAPI REST endpoints and an interactive web dashboard for head-to-head model comparison and failure root-cause analysis.
- **Pluggable Observability**: Non-intrusive Langfuse tracing with zero-overhead NoOp fallback.

---

## Architecture

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
           | queries                                                             | computes
           v                                                                     v
+---------------------+       +----------------------+                +---------------------+
|  Provider Factory   | ----> | Observability Layer  |                | Data Layer          |
| (OpenAI, Groq, Det) |       | (Langfuse & NoOp)    |                | (PostgreSQL/SQLite) |
+---------------------+       +----------------------+                +---------------------+
```

---

## Features

- [x] **50-Case Enterprise Benchmark Dataset (`benchmark_v1.json`)**: Real-world tasks across 8 business categories.
- [x] **Universal Provider Factory**: Supports OpenAI, Groq, Google Gemini, Ollama (local), Mock, and Deterministic CI providers.
- [x] **Modular Metric Evaluator Suite**: Exact Match, Substring Contains, Multiclass F1, Token Overlap Similarity, JSON Schema Validation, and LLM-as-a-Judge.
- [x] **Automated Regression Testing**: Configurable pass rate, latency, token usage, and quality score assertions with itemized failure analysis.
- [x] **Production REST API**: Fully documented OpenAPI/Swagger endpoints with Pydantic v2 schemas and dependency injection.
- [x] **Interactive Web Dashboard**: Accessible at `/dashboard` featuring overview KPIs, model comparison radar, category heatmaps, and failure logs.
- [x] **PostgreSQL & Alembic Migrations**: Normalized database schema preserving full experiment provenance.
- [x] **Zero-Quota GitHub Actions CI**: Deterministic offline pipeline enforcing regression thresholds on every push.
- [x] **Observability Tracing**: Langfuse trace/span collection with privacy filtering and graceful disconnection.

---

## Tech Stack

| Technology | Purpose | Rationale |
| :--- | :--- | :--- |
| **Python 3.12+** | Core Language | Modern async/await performance, type annotations, and scientific ecosystem. |
| **FastAPI** | REST API & Web Server | High-performance asynchronous routing, native Pydantic integration, and automatic OpenAPI generation. |
| **SQLAlchemy 2.0 & Alembic** | ORM & Migrations | Type-safe declarative models, seamless async/sync database interaction, and robust schema migrations. |
| **PostgreSQL & SQLite** | Persistence Engines | PostgreSQL for durable production runs; SQLite in-memory fallback for instantaneous, zero-dependency unit tests. |
| **Pydantic v2** | Data Validation & Schemas | High-speed Rust-based data validation and strict serialization of benchmark specs and metric payloads. |
| **Pandas** | Analysis & Reporting | Rapid tabular pivot, category aggregations, and automated CSV/JSON exports. |
| **Langfuse** | LLM Observability | Open-source, production-ready tracing of evaluation generations, latencies, and metadata. |
| **Pytest & Ruff** | QA & Linting | Comprehensive async test harness and sub-millisecond linting and code formatting. |
| **Docker & Docker Compose**| Containerization | Standardized multi-container orchestration for the FastAPI application and PostgreSQL database. |

---

## Evaluation Methodology

### 1. Dataset Design
The benchmark dataset (`datasets/benchmark_v1.json`) contains 50 synthetic test cases spanning 8 task categories:
- `factual question`: Knowledge retrieval and compliance policies.
- `classification`: Urgency detection, sentiment analysis, ticket routing.
- `extraction`: Structured JSON parsing and entity extraction.
- `instruction following`: Rigid negative and positive formatting constraints.
- `reasoning`: Mathematical deductions and multi-step logic.
- `customer support`: Tone, helpfulness, and policy escalation.
- `summarization`: Information density and brevity.
- `safety-sensitive response`: Prompt injection resistance and refusal behavior.

### 2. Evaluator Hierarchy
1. **Deterministic Rule Evaluators**: Run first for zero-cost, objective grading (exact string match, regex, JSON syntax, token count).
2. **Semantic Similarity Evaluators**: Token overlap and Jaccard similarity against reference answers.
3. **LLM-as-a-Judge**: Employs rubric-based structured scoring for subjective tasks (tone, policy adherence). Judge results provide explanatory reasoning alongside numerical scores.

### 3. Baseline vs. Candidate Benchmarking
- Experiments hold the dataset and test cases strictly constant.
- Variables under test: Model weights, provider endpoints, prompt template versions, or temperature/sampling parameters.

---

## Results

*Actual benchmark matrix results executed against `datasets/benchmark_v1.json` (50 test cases, Concurrency: 5):*

| Model / Configuration | Pass Rate | Avg Latency | Median Latency | Total Tokens | Estimated Cost | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`deterministic:perfect`** | **48.0%** | **15.9 ms** | **15.6 ms** | **2,972** | **\$0.0000** | Completed |
| **`mock:mock-v1`** | **26.0%** | **62.3 ms** | **61.8 ms** | **2,972** | **\$0.0000** | Completed |
| **`deterministic:degraded`** | **0.0%** | **15.8 ms** | **15.2 ms** | **2,750** | **\$0.0000** | Completed |

*Category-level breakdown of genuine run (`deterministic:perfect`):*
- **Instruction Following**: 66.7% pass rate
- **Factual Question**: 50.0% pass rate
- **Classification**: 57.1% pass rate
- **Extraction**: 42.9% pass rate
- **Reasoning**: 50.0% pass rate
- **Customer Support**: 33.3% pass rate

---

## Failure Analysis

The evaluation engine captures granular failure context for post-mortem debugging. Real failure examples:

### Case 1: Extraction Task (`EXTR-003`)
- **Input Prompt**: `Extract the invoice ID, amount, currency, and due date from this email: ...`
- **Expected Behavior**: Valid JSON object containing `invoice_id`, `amount`, `currency`, `due_date`.
- **Degraded Candidate Output**: `Degraded incomplete answer without required keywords or structure.`
- **Evaluator**: `JSONValidityEvaluator`
- **Failure Reason**: `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`
- **Score**: `0.00`

### Case 2: Classification Task (`CLAS-001`)
- **Input Prompt**: `Classify sentiment as POSITIVE, NEGATIVE, or NEUTRAL: 'The software crashes constantly.'`
- **Expected Behavior**: `NEGATIVE`
- **Candidate Output**: `POSITIVE` (or degraded text)
- **Evaluator**: `ClassificationEvaluator`
- **Failure Reason**: `Predicted class 'POSITIVE' did not match expected class 'NEGATIVE'.`
- **Score**: `0.00`

---

## Metric Limitations

1. **Small Dataset Size (50 cases)**: Provides rapid feedback for CI/CD, but is insufficient for high-statistical-power generalization across edge cases.
2. **Evaluator Bias in LLM Judges**: Models exhibit self-enhancement bias (scoring their own outputs higher) and length bias (favoring long answers over concise answers).
3. **Exact Match Rigidity**: Exact match yields false negatives when the LLM outputs semantically identical text with slight syntactic differences (e.g. `$100` vs `100 USD`).
4. **Keyword Matching Negation Failures**: Substring matching can trigger false passes or false fails when an LLM cites a prohibited keyword within a valid refusal disclaimer.
5. **Benchmark Contamination / Leakage**: Public benchmark questions may be present in base LLM pre-training corpuses.

---

## Reproducibility

Every evaluation run records:
- Git commit hash & dataset version tag (`v1`).
- Exact provider string (`openai`, `ollama`, `deterministic`) and model identifier.
- Full system prompt text and hyperparameter payload (`temperature`, `top_p`, `max_tokens`).
- Evaluation run UUID and per-case latency timestamps.

To reproduce any run:
```bash
python -m app evaluate \
  --dataset datasets/benchmark_v1.json \
  --provider deterministic \
  --model perfect \
  --output reports/reproduced_run.json
```

---

## Running Locally

### 1. Prerequisites
- Python 3.12+
- Docker & Docker Compose (optional for PostgreSQL)

### 2. Installation
```bash
# Clone repository
git clone https://github.com/your-org/llm-eval-platform.git
cd "llm-eval-platform"

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
```bash
cp .env.example .env
# Configure API keys in .env (OPENAI_API_KEY, GROQ_API_KEY, etc.)
```

### 4. Running the Web Application & Dashboard
```bash
uvicorn app.main:app --reload --port 8000
```
- Interactive API Docs: `http://localhost:8000/docs`
- Web Dashboard UI: `http://localhost:8000/dashboard`

### 5. Running via Docker Compose
```bash
docker compose up -d --build
```

---

## Testing

```bash
# 1. Run full unit and integration test suite
python -m pytest -v

# 2. Run deterministic evaluation CLI
python -m app evaluate --dataset datasets/benchmark_v1.json --provider deterministic --model perfect --limit 5

# 3. Run automated regression testing (Expect PASS -> Exit Code 0)
python -m app regression \
  --baseline-provider deterministic --baseline-model perfect \
  --candidate-provider deterministic --candidate-model perfect \
  --dataset datasets/benchmark_v1.json --limit 5 \
  --threshold-accuracy 0.80

# 4. Verify regression rejection (Expect FAIL -> Exit Code 1)
python -m app regression \
  --baseline-provider deterministic --baseline-model perfect \
  --candidate-provider deterministic --candidate-model degraded \
  --dataset datasets/benchmark_v1.json --limit 5 \
  --threshold-accuracy 0.85
```

---

## Architecture Decisions

1. **Zero-Quota Offline CI Design**: We built `DeterministicTestProvider` specifically to decouple CI pipelines from cloud LLM API availability and cost.
2. **Repository Pattern with Dual Engine Support**: Decoupled ORM persistence from business logic, allowing SQLite in-memory execution during tests and PostgreSQL in production.
3. **Pluggable Observability (Null Object Pattern)**: By implementing `NoOpObservability`, evaluation execution never crashes when Langfuse credentials are omitted.
4. **Exit-Code Gated CLI**: Built the regression CLI to emit POSIX-standard exit codes (`0` for PASS, `1` for FAIL) to integrate natively into any CI/CD orchestrator.

---

## Future Improvements

- [ ] **Embedding-Based Semantic Evaluator**: Integrate local ONNX/sentence-transformers for cosine semantic similarity without external API calls.
- [ ] **Dynamic Multi-Turn Dialogue Evaluation**: Extend dataset schema and runner to evaluate multi-turn conversational state machines.
- [ ] **Automated Dataset Perturbation & Robustness Testing**: Ingest adversarial typos and prompt injection perturbations to score model robustness.
- [ ] **Distributed Ray/Celery Task Workers**: Scale evaluation throughput to 10,000+ test cases across distributed worker clusters.
