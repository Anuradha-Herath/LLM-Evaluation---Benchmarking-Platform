# Benchmark Dataset Specifications & Versioning Policy

## 📌 Dataset Overview

The benchmark datasets in this directory serve as fixed, standardized test suites for evaluating and comparing LLM providers, prompt templates, and hyperparameter configurations in the **LLM Evaluation & Benchmarking Platform**.

The initial benchmark dataset (`benchmark_v1.json` & `benchmark_v1.csv`) contains **50 synthetic evaluation cases** focused on realistic business, technical, and customer-support tasks.

---

## 🏷️ Record Schema

Each evaluation case record follows a strict Pydantic contract (`DatasetRecord`):

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `string` | Unique identifier (e.g., `FACT-001`, `CUST-003`). Must be unique per dataset version. |
| `category` | `string` | Task category (one of 8 supported categories). |
| `input` | `string` | The exact prompt or context supplied to the LLM. |
| `expected_behavior` | `string` | Qualitative description of expected model behavior or success criteria. |
| `reference_answer` | `string \| null` | Gold-standard reference output used for similarity metrics or LLM-as-a-judge comparison. |
| `difficulty` | `string` | Task difficulty (`easy`, `medium`, `hard`). |
| `tags` | `string[]` | Domain and task tags (e.g. `["finance", "compliance"]`). |

---

## 🗂️ Task Categories

The dataset includes 50 cases evenly distributed across 8 core categories:

1. **`factual question`** (6 cases): Tests model precision, factual accuracy, and domain knowledge (e.g., ISO standards, GDPR, compliance).
2. **`summarization`** (6 cases): Evaluates conciseness and key insight extraction under strict length or format constraints.
3. **`classification`** (7 cases): Evaluates multi-class intent, sentiment, and urgency classification capabilities.
4. **`extraction`** (6 cases): Evaluates structured data extraction (JSON objects, regex entities, email lists, contract dates).
5. **`instruction following`** (6 cases): Tests adherence to complex formatting constraints, word limits, negative rules, and case formatting.
6. **`reasoning`** (6 cases): Evaluates multi-step mathematical calculations, logical deduction, and project scheduling critical paths.
7. **`customer support`** (7 cases): Tests empathy, de-escalation tone, and support troubleshooting clarity.
8. **`safety-sensitive response`** (6 cases): Evaluates model safety boundaries, refusal mechanisms, and compliant pivoting away from harmful prompts.

---

## 🔒 Immutability & Versioning Policy

> [!IMPORTANT]
> **Immutability Rule**: Once a benchmark version (e.g., `benchmark_v1`) is published, **it must remain strictly immutable**. Under no circumstances should existing records be modified, reordered, or deleted in place.

### Why Immutability is Enforced:
- **Reproducibility**: Historical benchmark runs executed against `v1` must yield directly comparable results over time.
- **Regression Detection**: Modifying test inputs or reference answers invalidates historical evaluation scores.

---

## 🚀 Creating Future Benchmark Versions (`benchmark_v2`)

When introducing new evaluation cases, expanded domains, or revised reference answers, follow these steps:

1. **Create New File**: Create `datasets/benchmark_v2.json` and `datasets/benchmark_v2.csv`.
2. **Increment Version Metadata**: Set `"version": "v2"` in the dataset metadata block.
3. **Maintain Schema Compliance**: Ensure all records pass validation via `DatasetLoader`.
4. **Document Changes**: Document added categories or modified evaluation targets in this README.

---

## ⚠️ Limitations & Scope

- **Synthetic Nature**: All records are synthetic examples created for benchmarking and contain zero real-world PII or proprietary data.
- **Domain Focus**: Primarily targets business workflows, IT support, financial communications, and developer tasks.
- **Static Coverage**: Benchmarks reflect a fixed point in time; emerging real-world edge cases should be captured in future dataset versions.
