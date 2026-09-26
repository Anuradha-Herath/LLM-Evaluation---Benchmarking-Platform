from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.provider import GenerationConfig


class ModelSpec(BaseModel):
    """
    Specification for a model/provider configuration in a benchmark matrix.
    """

    provider: str = Field(..., description="LLM provider name (e.g. 'openai', 'ollama', 'mock').")
    model: str = Field(..., description="Target model identifier.")
    config: GenerationConfig = Field(
        default_factory=GenerationConfig, description="Generation hyperparameters."
    )
    label: Optional[str] = Field(
        default=None, description="Human-readable label for reporting (e.g. 'GPT-4o Mini')."
    )


class PromptSpec(BaseModel):
    """
    Specification for a prompt template variant in a benchmark matrix.
    """

    name: str = Field(..., description="Prompt name.")
    version: str = Field(..., description="Prompt version tag.")
    system_prompt: Optional[str] = Field(
        default=None, description="System instructions prompt template text."
    )


class BenchmarkConfig(BaseModel):
    """
    Configuration payload for executing a multi-model/multi-prompt benchmark matrix.
    """

    dataset_path: Path = Field(..., description="Path to evaluation dataset JSON/CSV.")
    models: List[ModelSpec] = Field(..., description="List of model variants to evaluate.")
    prompts: List[PromptSpec] = Field(
        default_factory=lambda: [PromptSpec(name="Default Prompt", version="v1", system_prompt=None)],
        description="List of prompt variants to evaluate.",
    )
    concurrency: int = Field(default=5, ge=1, description="Concurrency limit.")
    limit: Optional[int] = Field(default=None, ge=1, description="Optional max test cases limit.")


class FailureCaseAnalysis(BaseModel):
    """
    Detailed payload describing a failed test case for root cause analysis.
    """

    case_id: str
    category: str
    provider: str
    model: str
    prompt_version: str
    expected_behavior: str
    actual_response: Optional[str] = None
    metric_results: Dict[str, float] = Field(default_factory=dict)
    error_message: Optional[str] = None


class RunComparisonStats(BaseModel):
    """
    Factual statistical comparison summary for a single experiment run.
    """

    run_id: str
    label: str
    provider: str
    model: str
    prompt_version: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate_pct: float
    avg_latency_ms: float
    median_latency_ms: float
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    category_scores: Dict[str, float] = Field(default_factory=dict)


class BenchmarkComparisonReport(BaseModel):
    """
    Complete benchmark comparison report bundle.
    """

    benchmark_name: str
    dataset_version: str
    total_experiments: int
    summary_runs: List[RunComparisonStats]
    failure_cases: List[FailureCaseAnalysis]
