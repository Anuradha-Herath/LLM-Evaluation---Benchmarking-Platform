from difflib import SequenceMatcher
from typing import Any, Optional
from app.evaluators.metrics.base import BaseMetric, MetricResult


class TextSimilarityMetric(BaseMetric):
    """
    Evaluates text similarity between candidate response and reference answer using combined SequenceMatcher ratio and Jaccard token overlap.
    """

    @property
    def name(self) -> str:
        return "text_similarity"

    @property
    def version(self) -> str:
        return "1.0.0"

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        if not set1 or not set2:
            return 0.0
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union)

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
                reasoning="No reference answer provided for similarity evaluation.",
            )

        # 1. SequenceMatcher ratio (Levenshtein / character gestalts)
        seq_ratio = SequenceMatcher(None, response_text.lower(), reference_answer.lower()).ratio()

        # 2. Jaccard token set similarity
        jaccard_ratio = self._jaccard_similarity(response_text, reference_answer)

        # Combined composite score (50% sequence ratio + 50% Jaccard)
        combined_score = round(0.5 * seq_ratio + 0.5 * jaccard_ratio, 4)
        passed = combined_score >= 0.60

        return MetricResult(
            metric_name=self.name,
            metric_version=self.version,
            score=combined_score,
            passed=passed,
            reasoning=f"Similarity score is {combined_score:.2f} (SeqMatcher: {seq_ratio:.2f}, Jaccard: {jaccard_ratio:.2f}).",
            metadata={
                "sequence_matcher_ratio": round(seq_ratio, 4),
                "jaccard_similarity": round(jaccard_ratio, 4),
            },
        )


class ResponseLengthMetric(BaseMetric):
    """
    Evaluates response character/word count against target min/max length constraints.
    """

    def __init__(
        self,
        min_words: Optional[int] = None,
        max_words: Optional[int] = None,
        exact_words: Optional[int] = None,
    ):
        self.min_words = min_words
        self.max_words = max_words
        self.exact_words = exact_words

    @property
    def name(self) -> str:
        return "response_length"

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
        min_w = kwargs.get("min_words", self.min_words)
        max_w = kwargs.get("max_words", self.max_words)
        exact_w = kwargs.get("exact_words", self.exact_words)

        words = response_text.strip().split()
        word_count = len(words)
        char_count = len(response_text)

        passed = True
        violations = []

        if exact_w is not None and word_count != exact_w:
            passed = False
            violations.append(f"Expected exactly {exact_w} words, but got {word_count}.")

        if min_w is not None and word_count < min_w:
            passed = False
            violations.append(f"Expected at least {min_w} words, but got {word_count}.")

        if max_w is not None and word_count > max_w:
            passed = False
            violations.append(f"Expected at most {max_w} words, but got {word_count}.")

        score = 1.0 if passed else 0.0
        reasoning = "Length constraints met." if passed else " ".join(violations)

        return MetricResult(
            metric_name=self.name,
            metric_version=self.version,
            score=score,
            passed=passed,
            reasoning=reasoning,
            metadata={
                "word_count": word_count,
                "char_count": char_count,
                "min_words": min_w,
                "max_words": max_w,
                "exact_words": exact_w,
            },
        )
