from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GenerationConfig(BaseModel):
    """
    Standard generation parameters across LLM providers.
    """

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for output randomness.",
    )
    max_tokens: Optional[int] = Field(
        default=1024,
        ge=1,
        description="Maximum number of tokens to generate.",
    )
    top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling probability density.",
    )
    frequency_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Penalty for token frequency.",
    )
    presence_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Penalty for token presence.",
    )
    stop: Optional[List[str]] = Field(
        default=None,
        description="List of stop sequences.",
    )
    timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        description="Request timeout in seconds.",
    )
    extra_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific additional parameters.",
    )


class LLMRequest(BaseModel):
    """
    Unified input schema for requesting LLM completions.
    """

    model: str = Field(..., description="Target model identifier (e.g. gpt-4o, llama3).")
    user_prompt: str = Field(..., description="Primary user input or query.")
    system_prompt: Optional[str] = Field(
        default=None, description="Optional system instructions or persona."
    )
    config: GenerationConfig = Field(
        default_factory=GenerationConfig,
        description="Generation hyperparameters.",
    )


class LLMResponse(BaseModel):
    """
    Unified response schema returned by all LLM providers.
    """

    text: str = Field(..., description="Generated text output from the model.")
    model: str = Field(..., description="Model identifier that produced the response.")
    provider_name: str = Field(..., description="Name of the LLM provider (e.g. openai, ollama, mock).")
    input_tokens: Optional[int] = Field(
        default=None, description="Number of prompt/input tokens processed."
    )
    output_tokens: Optional[int] = Field(
        default=None, description="Number of completion/output tokens generated."
    )
    total_tokens: Optional[int] = Field(
        default=None, description="Total token count (input + output)."
    )
    latency_ms: float = Field(
        ..., description="End-to-end request latency in milliseconds."
    )
    finish_reason: Optional[str] = Field(
        default=None, description="Reason for generation termination (e.g. stop, length)."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific metadata and raw metrics."
    )
    error: Optional[str] = Field(
        default=None, description="Error message if generation failed gracefully."
    )
