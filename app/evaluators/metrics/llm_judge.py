import json
import logging
import re
from typing import Any, Optional

from app.evaluators.metrics.base import BaseMetric, MetricResult
from app.providers.base import BaseLLMProvider
from app.schemas.provider import GenerationConfig, LLMRequest

logger = logging.getLogger("app.evaluators.metrics.llm_judge")

JUDGE_SYSTEM_PROMPT = """You are an expert AI Evaluation Judge.
Your job is to objectively evaluate an AI model's response based on the provided user query, expected behavior criteria, and optional reference answer.

You MUST respond ONLY with a valid JSON object matching this exact structure:
{
  "score": <float between 0.0 and 1.0>,
  "reasoning": "<detailed clear explanation of why this score was given>",
  "passed": <true or false>
}

Rubric:
- Score 1.0: Response completely satisfies the query, adheres to all expected behaviors, and is accurate.
- Score 0.7-0.9: Response satisfies the main query with minor non-critical flaws or slight formatting oversights.
- Score 0.4-0.6: Response partially answers the query but misses key instructions or contains partial inaccuracies.
- Score 0.0-0.3: Response is inaccurate, unhelpful, violates safety, or fails the query completely.
"""


class LLMJudgeMetric(BaseMetric):
    """
    Evaluates response quality using an LLM-as-a-judge model to produce structured scores and reasoning.
    """

    def __init__(
        self,
        judge_provider: BaseLLMProvider,
        judge_model: str,
        rubric_version: str = "1.0.0",
    ):
        self.judge_provider = judge_provider
        self.judge_model = judge_model
        self.rubric_version = rubric_version

    @property
    def name(self) -> str:
        return "llm_as_a_judge"

    @property
    def version(self) -> str:
        return self.rubric_version

    def _extract_json(self, text: str) -> dict:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        clean_text = match.group(1).strip() if match else text.strip()
        return json.loads(clean_text)

    async def evaluate(
        self,
        response_text: str,
        reference_answer: Optional[str] = None,
        expected_behavior: Optional[str] = None,
        **kwargs: Any,
    ) -> MetricResult:
        user_input = kwargs.get("user_input", "N/A")

        judge_prompt = f"""EVALUATION CASE:
User Input / Task: {user_input}
Expected Behavior: {expected_behavior or 'Satisfy user query accurately and concisely.'}
Reference Answer: {reference_answer or 'N/A'}

CANDIDATE RESPONSE TO EVALUATE:
{response_text}
"""

        request = LLMRequest(
            model=self.judge_model,
            user_prompt=judge_prompt,
            system_prompt=JUDGE_SYSTEM_PROMPT,
            config=GenerationConfig(temperature=0.1),
        )

        try:
            judge_resp = await self.judge_provider.generate(request)
            data = self._extract_json(judge_resp.text)

            score = float(data.get("score", 0.0))
            score = max(0.0, min(1.0, score))
            passed = bool(data.get("passed", score >= 0.7))
            reasoning = str(data.get("reasoning", "No reasoning provided by judge."))

            return MetricResult(
                metric_name=self.name,
                metric_version=self.version,
                score=score,
                passed=passed,
                reasoning=reasoning,
                metadata={
                    "rubric_version": self.rubric_version,
                    "judge_provider": self.judge_provider.provider_name,
                    "raw_judge_output": judge_resp.text,
                },
                judge_model=self.judge_model,
            )
        except Exception as exc:
            logger.error(f"LLM Judge evaluation failed: {exc}")
            return MetricResult(
                metric_name=self.name,
                metric_version=self.version,
                score=0.0,
                passed=False,
                reasoning=f"LLM Judge execution error: {exc}",
                metadata={"error": str(exc), "rubric_version": self.rubric_version},
                judge_model=self.judge_model,
            )
