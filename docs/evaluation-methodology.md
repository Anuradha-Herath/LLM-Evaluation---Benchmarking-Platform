# Evaluation Methodology Guide

## 1. Overview

Systematic LLM evaluation requires strict isolation of variables: dataset version, prompt version, model weights, and evaluator configuration must be tracked immutably.

---

## 2. Dataset Design (`benchmark_v1.json`)

The platform ships with a 50-case enterprise/customer-support dataset distributed across 8 core capability categories:

| Category | Count | Primary Objective | Key Evaluators Used |
| :--- | :--- | :--- | :--- |
| `factual question` | 6 | Accurate retrieval of domain knowledge & standards | `exact_match`, `contains`, `similarity` |
| `classification` | 7 | Intent routing, sentiment, urgency classification | `classification`, `exact_match` |
| `extraction` | 7 | Structured JSON / entity parsing | `json_validity`, `contains` |
| `instruction following` | 6 | Adherence to negative/positive formatting constraints | `exact_match`, `contains` |
| `reasoning` | 6 | Multi-step mathematical & logical deductions | `exact_match`, `contains` |
| `customer support` | 6 | Tone, resolution helpfulness, policy guidance | `similarity`, `llm_judge` |
| `summarization` | 6 | Information density & conciseness | `similarity`, `llm_judge` |
| `safety-sensitive` | 6 | Refusal of malicious injection & policy breach | `contains`, `llm_judge` |

---

## 3. Evaluation Pipeline

```
[Test Case Input] ──────> [Target LLM Provider] ──────> [Actual Output]
                                                               │
                                                               v
[Reference / Rubric] ─────────────────────────────────> [Metric Evaluators]
                                                               │
                                                               v
                                                    [Score & Pass/Fail Status]
```

### 3.1 Strict Isolation Rules
1. **Deterministic Prompts**: Prompts are parameterized with explicit variables without runtime string tampering.
2. **Fixed Seeds / Low Temperature**: Benchmarking runs use temperature `0.0` or fixed hyperparameters to maximize output stability.
3. **No Ground Truth Fabrication**: Non-deterministic categories use structured rubrics rather than fragile string matches.

---

## 4. LLM-as-a-Judge Protocol

For subjective tasks (customer support, summarization, safety), the platform includes an `LLMJudgeEvaluator`.

### Protocol Guidelines:
- **Never Ground Truth**: LLM-as-a-judge scores are treated as heuristic indicators, never ground truth.
- **Structured Schema**: The judge must return a strict JSON payload:
  ```json
  {
    "score": 0.85,
    "pass_fail": true,
    "reasoning": "The response accurately covers all three points without hallucinating extra terms.",
    "rubric_version": "v1.0"
  }
  ```
- **Judge Provenance**: The judge model identifier, prompt version, and rubric version are permanently recorded alongside the score.
