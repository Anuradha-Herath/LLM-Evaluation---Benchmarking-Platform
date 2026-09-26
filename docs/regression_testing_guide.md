# Automated LLM Regression Testing Guide

This guide explains how to set up, execute, and maintain automated regression tests for the **LLM Evaluation & Benchmarking Platform**.

---

## 📌 Core Concepts

### 1. Baseline
The **Baseline** represents your current production-grade model, prompt template, or hyperparameter configuration. It acts as the reference control against which all proposed changes are judged.

### 2. Candidate
The **Candidate** represents a proposed modification—such as an updated prompt template (`prompt_v2`), a newer model version (`gpt-4o` vs `gpt-3.5-turbo`), a fine-tuned checkpoint, or modified system instructions.

### 3. Thresholds
Quantitative constraints that candidate runs must satisfy. Common thresholds include:
- `min_pass_rate_pct`: Minimum acceptable percentage of test cases passed (e.g. 70%).
- `max_allowed_pass_rate_drop_pct`: Maximum permitted drop relative to baseline (e.g. 5.0%).
- `max_avg_latency_ms`: Maximum average response latency threshold (e.g. 1000ms).
- `max_latency_increase_pct`: Maximum allowed latency increase relative to baseline (e.g. 25%).
- `max_failure_rate_pct`: Maximum permitted error rate (e.g. 10%).

---

## 🛑 What Constitutes a Regression?

A **Regression** occurs when a candidate run violates one or more threshold assertions, indicating that the proposed change degrades quality, increases latency beyond acceptable bounds, or introduces new failure cases.

When a regression is detected:
1. The CLI tool prints an itemized **Violations Breakdown**.
2. The CLI returns a **non-zero exit code (`exit 1`)**, preventing automated deployment in CI/CD pipelines.

---

## 🔬 Managing Metric Instability & False Positives

### 1. LLM Sampling Variance
At `temperature > 0.0`, LLM outputs inherently possess stochastic variance. A candidate run might experience a transient 2% drop in pass rate due to random sampling noise rather than a prompt defect.

**Mitigations**:
- Set `temperature=0.0` or low values (`temperature=0.1`) during regression runs to maximize determinism.
- Use `max_allowed_pass_rate_drop_pct` buffer zones (e.g. 3-5%) rather than requiring strict `0.0%` tolerance.

### 2. False Positives in Lexical Metrics
Exact Match metrics can trigger false regression signals when a model generates a syntactically valid paraphrase of the reference answer.

**Mitigations**:
- Combine Exact Match with `TextSimilarityMetric` or `LLMJudgeMetric`.
- Periodically update gold-standard reference answers when model outputs produce valid alternatives.

---

## 🚀 Execution Commands

### Running Regression Tests via CLI

```bash
# Compare candidate against baseline using default thresholds
python -m app regression \
  --baseline-model mock:mock-model-v1 \
  --candidate-model mock:mock-model-v1 \
  --dataset datasets/benchmark_v1.json

# Override thresholds explicitly via CLI flags
python -m app regression \
  --baseline-model mock:mock-model-v1 \
  --candidate-model mock:mock-model-v2 \
  --max-avg-latency 50.0 \
  --min-pass-rate 80.0
```
