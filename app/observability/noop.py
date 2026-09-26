from typing import Any, Dict, Optional
from app.observability.base import BaseObservability


class NoOpObservability(BaseObservability):
    """
    Silent, zero-overhead Observability provider used when telemetry is disabled or credentials are absent.
    """

    def start_trace(
        self,
        run_id: str,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        pass

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
        pass

    def log_metric(
        self,
        run_id: str,
        case_id: str,
        metric_name: str,
        score: float,
        passed: Optional[bool] = None,
        reasoning: Optional[str] = None,
    ) -> None:
        pass

    def end_trace(self, run_id: str, status: str = "completed") -> None:
        pass

    def flush(self) -> None:
        pass
