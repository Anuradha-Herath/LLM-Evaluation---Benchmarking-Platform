# LLM Evaluation & Benchmarking Platform

A production-grade platform designed to systematically compare LLM models, prompts, and hyperparameter configurations using standardized datasets, automated & model-based evaluation metrics, observability integration, and regression testing.

---

## Technical Features & Skills Demonstrated

* **LLM API Integration**: Unified provider abstraction layer supporting both local models (Ollama/vLLM) and cloud APIs (OpenAI-compatible endpoints).
* **LLM Evaluation Engine**: Evaluation framework using rule-based metrics (exact match, similarity, JSON schema validation) and model-based metrics (DeepEval / Ragas).
* **Observability & Tracing**: Native Langfuse integration to log prompts, responses, latencies, token consumption, and evaluation scores.
* **Storage & Persistence**: PostgreSQL schema managed via SQLAlchemy & Alembic for tracking experiments, runs, and metric evaluations.
* **Automated Regression Testing**: Pytest suite for API endpoints and model performance thresholds.

---

## Directory Structure

```text
llm-evaluation-platform/
├── app/
│   ├── api/          # FastAPI routes & API endpoints (v1 health, experiments, datasets)
│   ├── core/         # Core application configuration (pydantic-settings, logging)
│   ├── db/           # Database sessions, connections, and migrations
│   ├── evaluators/   # Custom & automated evaluation metrics (DeepEval, rule-based)
│   ├── models/       # SQLAlchemy ORM models
│   ├── providers/    # LLM provider abstraction (Ollama, OpenAI, Mock)
│   ├── schemas/      # Pydantic schemas and request/response models
│   ├── services/     # Business logic & experiment orchestration services
│   └── main.py       # FastAPI application factory and entry point
├── datasets/         # Evaluation datasets (JSON/CSV format)
├── experiments/      # Experiment configuration definitions & benchmarks
├── tests/            # Pytest suite (unit & integration tests)
├── scripts/          # Helper scripts (dataset seeding, CLI evaluation runners)
├── reports/          # Generated evaluation reports and exports
├── docs/             # Technical design documents & architecture specs
├── docker/           # Dockerfiles & container assets
├── .env.example      # Template environment configuration file
├── docker-compose.yml# PostgreSQL Docker service definition
├── requirements.txt  # Python package dependencies
├── pyproject.toml    # Tooling config (Ruff, Pytest, metadata)
└── README.md         # Project documentation
```

---

## Setup & Quickstart Guide

### Prerequisites
* Python 3.12+
* Docker & Docker Compose (for PostgreSQL)
* Git

### 1. Clone & Environment Setup
```bash
# Copy template environment file
cp .env.example .env

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start PostgreSQL Database
```bash
docker compose up -d postgres
```

### 3. Run FastAPI Web Application
```bash
uvicorn app.main:app --reload
```
The server will start at `http://127.0.0.1:8000`. Access interactive API documentation at:
* Swagger UI: `http://127.0.0.1:8000/docs`
* ReDoc: `http://127.0.0.1:8000/redoc`

### 4. Run Test Suite
```bash
pytest
```

---

## Phased Development Roadmap

- [x] **Phase 0**: Project setup, directory structure, config, Docker, health endpoints & pytest framework.
- [ ] **Phase 1**: Database schema design, SQLAlchemy ORM models & Alembic migrations.
- [ ] **Phase 2**: LLM provider abstraction layer (Ollama local + OpenAI compatible).
- [ ] **Phase 3**: Dataset manager & batch experiment execution engine.
- [ ] **Phase 4**: Evaluators engine (rule-based, DeepEval / Ragas integration).
- [ ] **Phase 5**: Langfuse observability & automated regression test suite.
- [ ] **Phase 6**: Reporting & frontend visualization dashboard.
