# LLM Observability & Telemetry Integration Guide

This guide explains how to configure and inspect telemetry for the **LLM Evaluation & Benchmarking Platform** using **Langfuse**.

---

## 📌 Telemetry Data Specifications

### What IS Logged:
- **Trace Metadata**: Unique `run_id`, experiment name, benchmark dataset version, provider name, target model name, concurrency setting.
- **Generation Spans**: Individual test case ID (`case_id`), user input prompt, system prompt template, generated response text, latency in milliseconds (`latency_ms`), token consumption counts (`input_tokens`, `output_tokens`, `total_tokens`).
- **Error Telemetry**: Error messages, exception class names, HTTP status codes, retry counts.
- **Metric Scores**: Computed metric evaluation scores (`score`), boolean pass/fail status, reasoning rationales, and judge model names.

### What is NOT Logged (Scrubbed & Protected):
- **API Keys & Credentials**: `OPENAI_API_KEY`, `POSTGRES_PASSWORD`, `LANGFUSE_SECRET_KEY` are strictly excluded and automatically redacted (`[REDACTED]`) from all telemetry payloads.
- **Authorization Headers**: HTTP headers containing `Bearer` tokens or authentication strings.
- **Internal System Environment Variables**: Local database paths and operating system secrets.

---

## 🚀 How to Enable Langfuse Observability

### 1. Configure Environment Variables
To stream real-time traces to Langfuse Cloud or a self-hosted Langfuse instance, set the following variables in your `.env` file:

```env
LANGFUSE_PUBLIC_KEY=pk-lf-1234567890
LANGFUSE_SECRET_KEY=sk-lf-0987654321
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 2. Execution
Once keys are present, the application automatically detects them via `ObservabilityFactory` and initializes `LangfuseObservability`:

```bash
python -m app evaluate --dataset datasets/benchmark_v1.json --provider mock
```
Traces and generation spans will be streamed asynchronously to your Langfuse dashboard.

---

## 🛡️ Running Without Langfuse (Zero-Overhead / Offline Mode)

If `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are omitted or set to empty strings:
- The platform automatically selects `NoOpObservability`.
- All telemetry calls execute as zero-overhead pass-through methods.
- The evaluation engine operates at maximum speed with zero network latency overhead or external dependencies.
