# Experiment & Benchmark Execution Guide

## 1. Running Benchmark Comparisons

To compare multiple LLMs or prompt versions across a standard dataset:

```bash
# Compare OpenAI models against Ollama or Mock models
python -m app benchmark \
  --dataset datasets/benchmark_v1.json \
  --models "openai:gpt-4o-mini,openai:gpt-4o,mock:mock-v1" \
  --concurrency 3 \
  --output-dir reports
```

This generates three artifacts in `reports/`:
1. `benchmark_results.csv`: Granular row-by-row outputs, scores, latencies, and tokens for every test case.
2. `benchmark_summary.csv`: Aggregated model comparisons (pass rates, latency percentiles, cost, category scores).
3. `benchmark_report.json`: Full nested schema with failure case analyses.

---

## 2. Web Dashboard Walkthrough

Start the FastAPI application and navigate to the interactive engineering dashboard:

```bash
# Start server
uvicorn app.main:app --reload --port 8000
```
Open **`http://localhost:8000/dashboard`** in your browser to view:
- **System Overview KPI Cards**: Total experiments, overall pass rate, average latency, and cost estimates.
- **Model Comparison Radar & Bar Charts**: Head-to-head comparison across categories (Reasoning, Extraction, Classification).
- **Category Performance Heatmap**: Breakdown of strengths and failure concentrations.
- **Failure Analysis & Debugging Log**: Direct inspection of prompt inputs, expected vs actual outputs, and error traces.

---

## 3. Database Persistence & SQL Queries

Evaluation runs are persisted in PostgreSQL. Useful SQL queries for analytics:

```sql
-- Average pass rate and latency by model
SELECT 
    model,
    provider,
    COUNT(id) AS total_runs,
    AVG(pass_rate_pct) AS avg_pass_rate,
    AVG(avg_latency_ms) AS avg_latency
FROM evaluation_runs
GROUP BY model, provider;

-- Identify frequently failing test cases
SELECT 
    test_case_id,
    COUNT(*) AS total_failures,
    COUNT(DISTINCT run_id) AS failed_in_runs
FROM evaluation_results
WHERE error IS NOT NULL
GROUP BY test_case_id
ORDER BY total_failures DESC;
```
