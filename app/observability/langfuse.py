import logging
from typing import Any, Dict, Optional

from app.core.config import settings
from app.observability.base import BaseObservability

logger = logging.getLogger("app.observability.langfuse")


class LangfuseObservability(BaseObservability):
    """
    LLM Observability provider sending telemetry traces, generation spans, and evaluation metrics to Langfuse.
    """

    def __init__(
        self,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
        client: Optional[Any] = None,
    ):
        self.public_key = public_key or settings.LANGFUSE_PUBLIC_KEY
        self.secret_key = secret_key or settings.LANGFUSE_SECRET_KEY
        self.host = host or settings.LANGFUSE_HOST

        self._client = client
        self._traces: Dict[str, Any] = {}
        self._spans: Dict[str, Any] = {}

        if self._client is None and self.public_key and self.secret_key:
            try:
                from langfuse import Langfuse
                self._client = Langfuse(
                    public_key=self.public_key,
                    secret_key=self.secret_key,
                    host=self.host,
                )
                logger.info(f"Initialized Langfuse client targeting {self.host}")
            except Exception as exc:
                logger.warning(f"Could not initialize Langfuse SDK: {exc}. Telemetry will be buffered locally.")

    def _sanitize_metadata(self, metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Scrubs sensitive credentials, bearer tokens, or secret keys from telemetry metadata."""
        if not metadata:
            return {}
        clean_meta = {}
        for k, v in metadata.items():
            if any(secret_kw in k.lower() for secret_kw in ["key", "secret", "password", "token", "auth"]):
                clean_meta[k] = "[REDACTED]"
            else:
                clean_meta[k] = v
        return clean_meta

    def start_trace(
        self,
        run_id: str,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            clean_meta = self._sanitize_metadata(metadata)
            if self._client and hasattr(self._client, "trace"):
                trace = self._client.trace(
                    id=run_id,
                    name=name,
                    metadata=clean_meta,
                )
                self._traces[run_id] = trace
            else:
                self._traces[run_id] = {"id": run_id, "name": name, "metadata": clean_meta, "spans": []}
            logger.debug(f"Started Langfuse trace '{name}' (run_id={run_id})")
        except Exception as exc:
            logger.error(f"Error starting Langfuse trace: {exc}")

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
        try:
            span_key = f"{run_id}:{case_id}"
            trace = self._traces.get(run_id)

            if trace and hasattr(trace, "generation"):
                gen_span = trace.generation(
                    name=f"case:{case_id}",
                    model=model,
                    input=[
                        {"role": "system", "content": system_prompt} if system_prompt else None,
                        {"role": "user", "content": user_prompt},
                    ],
                    output=response_text or error,
                    usage={
                        "input": input_tokens or 0,
                        "output": output_tokens or 0,
                        "unit": "TOKENS",
                    },
                    metadata={"case_id": case_id, "latency_ms": latency_ms, "error": error},
                )
                self._spans[span_key] = gen_span
            else:
                span_data = {
                    "case_id": case_id,
                    "model": model,
                    "user_prompt": user_prompt,
                    "system_prompt": system_prompt,
                    "response_text": response_text,
                    "latency_ms": latency_ms,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "error": error,
                }
                self._spans[span_key] = span_data
                if isinstance(trace, dict):
                    trace["spans"].append(span_data)

            logger.debug(f"Logged Langfuse generation span for case '{case_id}'")
        except Exception as exc:
            logger.error(f"Error logging Langfuse generation: {exc}")

    def log_metric(
        self,
        run_id: str,
        case_id: str,
        metric_name: str,
        score: float,
        passed: Optional[bool] = None,
        reasoning: Optional[str] = None,
    ) -> None:
        try:
            span_key = f"{run_id}:{case_id}"
            span = self._spans.get(span_key)

            if span and hasattr(span, "score"):
                span.score(
                    name=metric_name,
                    value=score,
                    comment=reasoning,
                )
            elif isinstance(span, dict):
                if "scores" not in span:
                    span["scores"] = []
                span["scores"].append({
                    "name": metric_name,
                    "value": score,
                    "passed": passed,
                    "comment": reasoning,
                })
            logger.debug(f"Logged Langfuse metric '{metric_name}' ({score}) for case '{case_id}'")
        except Exception as exc:
            logger.error(f"Error logging Langfuse score: {exc}")

    def end_trace(self, run_id: str, status: str = "completed") -> None:
        try:
            trace = self._traces.get(run_id)
            if trace and hasattr(trace, "update"):
                trace.update(metadata={"final_status": status})
            elif isinstance(trace, dict):
                trace["status"] = status
            logger.debug(f"Ended Langfuse trace '{run_id}' with status '{status}'")
        except Exception as exc:
            logger.error(f"Error ending Langfuse trace: {exc}")

    def flush(self) -> None:
        try:
            if self._client and hasattr(self._client, "flush"):
                self._client.flush()
                logger.info("Flushed telemetry traces to Langfuse backend.")
        except Exception as exc:
            logger.error(f"Error flushing Langfuse client: {exc}")
