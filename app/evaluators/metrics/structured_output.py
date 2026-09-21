import json
import re
from typing import Any, List, Optional
from app.evaluators.metrics.base import BaseMetric, MetricResult


class JSONValidityMetric(BaseMetric):
    """
    Evaluates whether the LLM response is valid JSON and contains required keys.
    """

    def __init__(self, required_keys: Optional[List[str]] = None):
        self.required_keys = required_keys or []

    @property
    def name(self) -> str:
        return "json_validity"

    @property
    def version(self) -> str:
        return "1.0.0"

    def _extract_json_str(self, text: str) -> str:
        if not text:
            return ""
        text = text.strip()
        # Extract markdown json fence blocks
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text

    async def evaluate(
        self,
        response_text: str,
        reference_answer: Optional[str] = None,
        expected_behavior: Optional[str] = None,
        **kwargs: Any,
    ) -> MetricResult:
        req_keys = kwargs.get("required_keys", self.required_keys)
        raw_json = self._extract_json_str(response_text)

        try:
            parsed = json.loads(raw_json)
            is_valid_json = True
            parse_error = None
        except Exception as exc:
            parsed = None
            is_valid_json = False
            parse_error = str(exc)

        if not is_valid_json:
            return MetricResult(
                metric_name=self.name,
                metric_version=self.version,
                score=0.0,
                passed=False,
                reasoning=f"Invalid JSON syntax: {parse_error}",
                metadata={"valid_json": False, "parse_error": parse_error},
            )

        missing_keys = []
        if req_keys and isinstance(parsed, dict):
            for k in req_keys:
                if k not in parsed:
                    missing_keys.append(k)

        if missing_keys:
            key_score = max(0.0, (len(req_keys) - len(missing_keys)) / len(req_keys))
            return MetricResult(
                metric_name=self.name,
                metric_version=self.version,
                score=round(key_score, 4),
                passed=False,
                reasoning=f"JSON valid, but missing required key(s): {missing_keys}",
                metadata={
                    "valid_json": True,
                    "missing_keys": missing_keys,
                    "found_keys": list(parsed.keys()),
                },
            )

        return MetricResult(
            metric_name=self.name,
            metric_version=self.version,
            score=1.0,
            passed=True,
            reasoning="Output is valid JSON and contains all required keys.",
            metadata={
                "valid_json": True,
                "parsed_type": type(parsed).__name__,
                "keys_present": list(parsed.keys()) if isinstance(parsed, dict) else None,
            },
        )
