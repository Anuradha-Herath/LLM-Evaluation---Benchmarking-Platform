# CI/CD and Deterministic Testing Guide

This guide details the continuous integration, continuous delivery, and regression testing architecture for the **LLM Evaluation & Benchmarking Platform**.

---

## 1. Design Philosophy: Zero Quota Wastage in CI

A critical architectural constraint for LLM engineering platforms:
- **Normal CI (PRs & Pushes) must NEVER make paid or rate-limited external LLM API calls.**
- Consuming external LLM quotas (Gemini, Groq, OpenAI) on every commit introduces flakiness, rate limits, latency, cost spikes, and broken builds when API keys expire or throttle.
- Instead, automated CI uses **Deterministic Test Providers** (`DeterministicTestProvider` / `MockLLMProvider`) to execute full unit, integration, database, metric computation, and regression assertion pipelines 100% offline with zero network latency.
- Live LLM model evaluations are segregated into an **On-Demand Manual Workflow** (`workflow_dispatch`).

---

## 2. CI Architecture Overview

```
                        GitHub Actions Pipeline
                       =========================
                                  │
          ┌───────────────────────┴───────────────────────┐
          │                                               │
   [Automated CI Workflow]                     [Manual Benchmark Workflow]
   (.github/workflows/ci.yml)            (.github/workflows/benchmark_manual.yml)
          │                                               │
   Trigger: Push / PR                          Trigger: workflow_dispatch
          │                                               │
   ├── 1. Code Linting (Ruff)                  ├── 1. Load Repository Secrets
   ├── 2. Test Suite (pytest, DB, API)         ├── 2. Target Live LLM (OpenAI/Groq/Gemini)
   ├── 3. Deterministic Evaluation Run         ├── 3. Rate-limited concurrent runner
   ├── 4. Deterministic Regression Assertion   ├── 4. Upload JSON/CSV artifacts
   └── 5. Negative Gate Validation (Exit != 0) └── 5. Step Summary to GitHub PR/Run
```

---

## 3. Deterministic Test Provider Modes

The `DeterministicTestProvider` (`app/providers/deterministic_provider.py`) allows testing every phase of the evaluation engine without external dependencies:

| Mode | Behavior | Use Case in CI |
| :--- | :--- | :--- |
| `perfect` | Generates canonical answers, high accuracy, clean JSON, valid classifications | Baseline runs and positive regression passes |
| `degraded` | Simulates prompt regression / degraded model accuracy (`[DEGRADED_OUTPUT]`) | Verifying CI gates fail on quality degradation |
| `slow` | Injects synthetic latency (e.g. 500ms) | Validating latency regression assertions |
| `error` | Simulates provider upstream API 500 errors | Testing engine resilience and error logging |
| `timeout` | Simulates provider timeout exceptions | Testing timeout thresholds and partial recovery |

---

## 4. GitHub Actions Workflows

### 4.1 CI Workflow (`.github/workflows/ci.yml`)

Runs automatically on every `push` and `pull_request` to `main`, `master`, and `dev` branches:
1. **Environment Setup:** Python 3.12, dependency caching.
2. **Linting:** Runs `ruff check .` across all Python source code.
3. **Automated Testing:** Runs `pytest` testing database models, API routes, metric functions, and engine services.
4. **Deterministic Evaluation:** Runs `python -m app eval` using the `deterministic:perfect` model against `benchmark_v1.json`.
5. **Deterministic Regression Gate:** Runs `python -m app regression` comparing `deterministic:perfect` against itself. Enforces thresholds:
   - `accuracy >= 0.80`
   - `failure_rate <= 0.05`
6. **Negative Verification Step:** Runs a candidate with `deterministic:degraded` to verify that the CLI outputs exit code `1` and would catch a genuine regression.

### 4.2 Manual Benchmark Workflow (`.github/workflows/benchmark_manual.yml`)

Runs on demand when a developer or ML engineer wants to run a live evaluation against production endpoints:
- **Inputs:**
  - `provider`: `openai`, `groq`, `gemini`, `ollama`, `mock`, `deterministic`
  - `model`: e.g. `gpt-4o-mini`, `llama-3.3-70b-versatile`, `gemini-2.0-flash`
  - `dataset_path`: `datasets/benchmark_v1.json`
  - `eval_limit`: optional case limit (e.g. `10` or `50`)
  - `concurrency`: default `2` to respect provider RPM/TPM limits.
- **Outputs:**
  - Saves artifacts in `reports/manual_benchmark_results.json`
  - Renders markdown summary table directly to the GitHub Action run summary.

---

## 5. Secret Management & Rate Limiting

### 5.1 Required Repository Secrets

When running manual benchmarks on GitHub Actions, configure the following secrets in **Settings -> Secrets and variables -> Actions**:

| Secret Name | Description |
| :--- | :--- |
| `OPENAI_API_KEY` | OpenAI API access token for GPT models |
| `GROQ_API_KEY` | GroqCloud API key for Llama / Mixtral inference |
| `GEMINI_API_KEY` | Google Gemini API key |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key (optional observability) |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key (optional observability) |
| `LANGFUSE_HOST` | Langfuse server URL (defaults to `https://cloud.langfuse.com`) |

### 5.2 Secret Protection Rules
- **Never echo secrets** in bash/powershell run steps.
- **Never log API responses containing prompt credentials.**
- When running observability traces, headers containing authorization tokens are stripped before forwarding.

### 5.3 Rate-Limit Handling Strategies
- **Concurrency control:** Evaluation engine uses an `asyncio.Semaphore` (configurable via `--concurrency 2` or `EVAL_CONCURRENCY=2`).
- **Exponential Backoff:** The provider client automatically retries on HTTP 429 (Too Many Requests) with jittered exponential backoff.
- **Fail-safe batching:** Test cases that experience non-retryable errors are logged with `error` fields in `EvaluationResult` without crashing the entire batch run.

---

## 6. Running Local Verification Commands

To test the complete CI pipeline locally:

```bash
# 1. Run linter
ruff check .

# 2. Run unit tests
pytest -v

# 3. Run deterministic evaluation
python -m app evaluate --dataset datasets/benchmark_v1.json --provider deterministic --model perfect --limit 5

# 4. Run deterministic regression check (Expect Exit Code 0 - PASS)
python -m app regression \
  --baseline-provider deterministic --baseline-model perfect \
  --candidate-provider deterministic --candidate-model perfect \
  --dataset datasets/benchmark_v1.json --limit 5 \
  --threshold-accuracy 0.8
```
