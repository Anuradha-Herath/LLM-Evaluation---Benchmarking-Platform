from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseObservability(ABC):
    """
    Abstract Base Class defining the contract for LLM Observability & Telemetry providers.
    """

    @abstractmethod
    def start_trace(
        self,
        run_id: str,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Starts a top-level evaluation experiment trace.

        :param run_id: Unique evaluation run identifier.
        :param name: Human-readable trace name.
        :param metadata: Contextual metadata dictionary.
        """
        pass

    @abstractmethod
    def log_generation(
        self,
        run_id: str,
        case_id: str,
        model: str,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        response_text: Optional[str] = None,
        latency_ms: float = 0.0,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Logs an individual LLM generation call span under the active trace.

        :param run_id: Active evaluation run ID.
        :param case_id: Benchmark test case ID.
        :param model: Target model identifier.
        :param user_prompt: User input prompt.
        :param system_prompt: Optional system instructions prompt.
        :param response_text: LLM response output text.
        :param latency_ms: Latency in milliseconds.
        :param input_tokens: Prompt token count.
        :param output_tokens: Generated token count.
        :param error: Error message string if generation failed.
        """
        pass

    @abstractmethod
    def log_metric(
        self,
        run_id: str,
        case_id: str,
        metric_name: str,
        score: float,
        passed: Optional[bool] = None,
        reasoning: Optional[str] = None,
    ) -> None:
        """
        Logs a metric evaluation score for a test case.

        :param run_id: Active evaluation run ID.
        :param case_id: Benchmark test case ID.
        :param metric_name: Name of the evaluation metric.
        :param score: Score value (0.0 - 1.0).
        :param passed: Pass/fail boolean status.
        :param reasoning: Evaluation rationale text.
        """
        pass

    @abstractmethod
    def end_trace(self, run_id: str, status: str = "completed") -> None:
        """
        Finalizes the evaluation experiment trace.

        :param run_id: Unique evaluation run identifier.
        :param status: Final status string ('completed', 'failed', 'partial_failure').
        """
        pass

    @abstractmethod
    def flush(self) -> None:
        """
        Flushes all buffered traces to the remote observability backend.
        """
        pass
