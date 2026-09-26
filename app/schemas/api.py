from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

from app.schemas.provider import GenerationConfig

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated API response container.
    """

    items: List[T]
    total: int = Field(..., ge=0, description="Total number of items available.")
    limit: int = Field(..., ge=1, description="Page limit.")
    offset: int = Field(..., ge=0, description="Page offset.")


class EvaluationCreateRequest(BaseModel):
    """
    Request payload to trigger a single evaluation run.
    """

    dataset_path: str = Field(
        default="datasets/benchmark_v1.json",
        description="Path to benchmark dataset file.",
    )
    provider: str = Field(default="mock", description="Target LLM provider name ('mock', 'openai', 'ollama').")
    model: str = Field(default="mock-model-v1", description="Target model identifier.")
    system_prompt: Optional[str] = Field(
        default=None, description="Optional system instructions prompt."
    )
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature.")
    concurrency: int = Field(default=5, ge=1, le=20, description="Max concurrent request workers.")
    persist_db: bool = Field(default=True, description="Whether to persist run into PostgreSQL database.")


class BenchmarkCreateRequest(BaseModel):
    """
    Request payload to trigger a multi-model benchmark comparison matrix.
    """

    dataset_path: str = Field(
        default="datasets/benchmark_v1.json",
        description="Path to benchmark dataset file.",
    )
    models: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"provider": "mock", "model": "mock-model-v1", "label": "Model A (V1)"},
            {"provider": "mock", "model": "mock-model-v2", "label": "Model B (V2)"},
        ],
        description="List of provider:model dictionary specifications.",
    )
    prompts: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of prompt dictionary specifications.",
    )
    concurrency: int = Field(default=5, ge=1, le=20, description="Max concurrent workers.")


class RegressionTestApiRequest(BaseModel):
    """
    Request payload to execute an automated regression test comparison.
    """

    dataset_path: str = Field(
        default="datasets/benchmark_v1.json",
        description="Path to benchmark dataset file.",
    )
    baseline_model: str = Field(
        default="mock:mock-model-v1", description="Baseline provider:model string."
    )
    candidate_model: str = Field(
        default="mock:mock-model-v1", description="Candidate provider:model string."
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional regression threshold parameters overrides."
    )
