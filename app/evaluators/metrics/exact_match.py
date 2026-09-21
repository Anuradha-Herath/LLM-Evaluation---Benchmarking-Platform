import string
from typing import Any, List, Optional
from app.evaluators.metrics.base import BaseMetric, MetricResult


class ExactMatchMetric(BaseMetric):
    """
    Evaluates whether the candidate response matches the reference answer exactly (with normalization options).
    """

    def __init__(
        self,
        case_sensitive: bool = False,
        ignore_punctuation: bool = True,
        strip_whitespace: bool = True,
    ):
        self.case_sensitive = case_sensitive
        self.ignore_punctuation = ignore_punctuation
        self.strip_whitespace = strip_whitespace

    @property
    def name(self) -> str:
        return "exact_match"

    @property
    def version(self) -> str:
        return "1.0.0"

    def _normalize(self, text: str) -> str:
        if not text:
            return ""
        if self.strip_whitespace:
            text = text.strip()
        if not self.case_sensitive:
            text = text.lower()
        if self.ignore_punctuation:
            text = text.translate(str.maketrans("", "", string.punctuation))
        return " ".join(text.split())

    async def evaluate(
        self,
        response_text: str,
        reference_answer: Optional[str] = None,
        expected_behavior: Optional[str] = None,
        **kwargs: Any,
    ) -> MetricResult:
        if not reference_answer:
            return MetricResult(
                metric_name=self.name,
                metric_version=self.version,
                score=0.0,
                passed=False,
                reasoning="No reference answer provided for exact match evaluation.",
            )

        norm_resp = self._normalize(response_text)
        norm_ref = self._normalize(reference_answer)

        matched = norm_resp == norm_ref
        score = 1.0 if matched else 0.0

        return MetricResult(
            metric_name=self.name,
            metric_version=self.version,
            score=score,
            passed=matched,
            reasoning=f"Exact match {'succeeded' if matched else 'failed'}.",
            metadata={
                "normalized_response": norm_resp,
                "normalized_reference": norm_ref,
                "case_sensitive": self.case_sensitive,
                "ignore_punctuation": self.ignore_punctuation,
            },
        )


class ContainsKeywordMetric(BaseMetric):
    """
    Evaluates what percentage of specified required keywords/phrases appear in the candidate response.
    """

    def __init__(self, default_keywords: Optional[List[str]] = None, case_sensitive: bool = False):
        self.default_keywords = default_keywords or []
        self.case_sensitive = case_sensitive

    @property
    def name(self) -> str:
        return "contains_keyword"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def evaluate(
        self,
        response_text: str,
        reference_answer: Optional[str] = None,
        expected_behavior: Optional[str] = None,
        **kwargs: Any,
    ) -> MetricResult:
        keywords = kwargs.get("keywords", self.default_keywords)

        # Fallback: if no explicit keywords list provided, extract non-stop words from reference_answer
        if not keywords and reference_answer:
            keywords = [w.strip() for w in reference_answer.split() if len(w.strip()) > 3]

        if not keywords:
            return MetricResult(
                metric_name=self.name,
                metric_version=self.version,
                score=0.0,
                passed=False,
                reasoning="No keywords supplied for contains metric evaluation.",
            )

        text = response_text if self.case_sensitive else response_text.lower()
        found = []
        missing = []

        for kw in keywords:
            target_kw = kw if self.case_sensitive else kw.lower()
            if target_kw in text:
                found.append(kw)
            else:
                missing.append(kw)

        score = round(len(found) / len(keywords), 4)
        passed = len(missing) == 0

        return MetricResult(
            metric_name=self.name,
            metric_version=self.version,
            score=score,
            passed=passed,
            reasoning=f"Found {len(found)}/{len(keywords)} expected keywords.",
            metadata={
                "found_keywords": found,
                "missing_keywords": missing,
                "total_keywords": len(keywords),
            },
        )
