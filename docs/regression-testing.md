# Automated LLM Regression Testing Guide

## 1. Concept: Quality Gates for AI Systems

In traditional software, tests assert binary deterministic functions. In LLM applications, changes to system prompts, model weights, or formatting instructions introduce subtle regressions (e.g. classification drop, JSON schema invalidity, latency inflation).

The regression testing engine provides **automated quality gating** with non-zero exit codes suitable for CI/CD pipelines.

---

## 2. Regression Configuration Schema

Regression assertions are configured via `RegressionConfig` or passed via CLI flags:

```json
{
  "min_pass_rate_pct": 75.0,
  "max_failure_rate_pct": 5.0,
  "max_avg_latency_ms": 1500.0,
  "max_allowed_pass_rate_drop_pct": 5.0,
  "max_latency_increase_pct": 20.0,
  "min_avg_metric_score": 0.80
}
```

---

## 3. Execution Workflows

### 3.1 CLI Execution
```bash
# Compare a prompt variant against baseline
python -m app regression \
  --dataset datasets/benchmark_v1.json \
  --baseline-model deterministic:perfect \
  --candidate-model deterministic:degraded \
  --threshold-accuracy 0.80
```

### 3.2 Regression Violation Breakdown Output
When an assertion fails, the CLI outputs a detailed violation matrix and exits with status code `1`:

```
----------------------------------------------------------------------
  REGRESSION TEST STATUS: FAIL
----------------------------------------------------------------------
 Summary: Regression evaluation FAILED with 2 threshold violation(s).

VIOLATIONS BREAKDOWN:
Metric                 | Baseline   | Candidate  | Abs Diff   | Pct Diff  
----------------------------------------------------------------------
latency_increase_pct   |      10.88 |      14.49 |      +3.61 |    +33.18%
  -> Threshold Rule: latency increase (33.2%) <= max_allowed_increase (25.0%)
avg_quality_score      |       1.00 |       0.00 |      -1.00 |   -100.00%
  -> Threshold Rule: candidate avg quality score (0.00) >= min_avg_metric_score (0.80)
  -> Affected Test Cases (5): ['CLAS-001', 'CLAS-002', 'CLAS-003', 'CLAS-004', 'CLAS-005']
----------------------------------------------------------------------
[FAIL] REGRESSION DETECTED! Exiting with non-zero exit code (1) for CI/CD gating.
```

---

## 4. CI/CD Pipeline Integration

The GitHub Actions CI workflow runs regression checks on every PR without calling external APIs using `DeterministicTestProvider`. This ensures PRs that degrade prompt formatting or classification handling are automatically rejected.
