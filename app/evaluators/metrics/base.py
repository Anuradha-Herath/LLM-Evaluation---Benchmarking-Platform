from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class MetricResult(BaseModel):
    """
    Standardized payload returned by all evaluation metrics.
    """

    metric_name: str = Field(..., description="Canonical metric name.")
    metric_version: str = Field(..., description="Version of the metric implementation.")
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized score between 0.0 and 1.0.")
    passed: Optional[bool] = Field(
        default=None, description="Optional boolean pass/fail status."
    )
    reasoning: Optional[str] = Field(
        default=None, description="Explanation or rationale for the assigned score."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Metric-specific calculation details and context."
    )
    judge_model: Optional[str] = Field(
        default=None, description="Model identifier if LLM-as-a-judge was used."
    )


class BaseMetric(ABC):
    """
    Abstract Base Class for all evaluation metrics.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Canonical metric identifier name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Metric version string."""
        pass

    @abstractmethod
    async def evaluate(
        self,
        response_text: str,
        reference_answer: Optional[str] = None,
        expected_behavior: Optional[str] = None,
        **kwargs: Any,
    ) -> MetricResult:
        """
        Evaluates a candidate response against reference materials or behavioral criteria.

        :param response_text: Raw LLM output string to evaluate.
        :param reference_answer: Optional ground truth gold-standard reference.
        :param expected_behavior: Optional qualitative description of expected behavior.
        :param kwargs: Additional metric-specific contextual arguments.
        :return: MetricResult object.
        """
        pass
