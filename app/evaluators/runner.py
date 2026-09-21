import asyncio
import logging
from typing import Optional

from app.core.exceptions import (
    LLMProviderError,
    LLMProviderRateLimitError,
    LLMProviderTimeoutError,
)
from app.evaluators.result import EvaluationResult
from app.providers.base import BaseLLMProvider
from app.schemas.dataset import DatasetRecord
from app.schemas.provider import GenerationConfig, LLMRequest

logger = logging.getLogger("app.evaluators.runner")


class CaseRunner:
    """
    Executes an individual evaluation test case against an LLM provider with retry logic and fault isolation.
    """

    @classmethod
    async def run_case(
        cls,
        run_id: str,
        record: DatasetRecord,
        provider: BaseLLMProvider,
        model: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        max_retries: int = 2,
        initial_backoff_sec: float = 0.5,
    ) -> EvaluationResult:
        """
        Executes a single test case record with retries and fault isolation.

        :param run_id: Active evaluation run ID.
        :param record: Dataset test case record.
        :param provider: Initialized BaseLLMProvider instance.
        :param model: Target model identifier.
        :param system_prompt: System instructions prompt template.
        :param config: Generation configuration hyperparameters.
        :param max_retries: Number of retry attempts on transient failures.
        :param initial_backoff_sec: Base backoff time in seconds.
        :return: EvaluationResult object representing case outcome.
        """
        gen_config = config or GenerationConfig()
        request = LLMRequest(
            model=model,
            user_prompt=record.input,
            system_prompt=system_prompt,
            config=gen_config,
        )

        last_error_msg: Optional[str] = None
        attempt = 0

        while attempt <= max_retries:
            attempt += 1
            try:
                logger.debug(
                    f"Executing case '{record.id}' (Attempt {attempt}/{max_retries + 1})"
                )
                response = await provider.generate(request)

                return EvaluationResult(
                    run_id=run_id,
                    test_case_id=record.id,
                    response=response.text,
                    latency_ms=response.latency_ms,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    total_tokens=response.total_tokens,
                    error=response.error,
                )

            except (LLMProviderTimeoutError, LLMProviderRateLimitError) as exc:
                last_error_msg = f"{exc.__class__.__name__}: {exc.message}"
                if attempt <= max_retries:
                    backoff = initial_backoff_sec * (2 ** (attempt - 1))
                    logger.warning(
                        f"Transient error on case '{record.id}' (Attempt {attempt}): {last_error_msg}. Retrying in {backoff:.2f}s..."
                    )
                    await asyncio.sleep(backoff)
                else:
                    logger.error(
                        f"Max retries reached for case '{record.id}'. Failing with error: {last_error_msg}"
                    )

            except LLMProviderError as exc:
                # Permanent provider error (e.g. 404 model not found, invalid key)
                last_error_msg = f"{exc.__class__.__name__}: {exc.message}"
                logger.error(
                    f"Non-retryable provider error on case '{record.id}': {last_error_msg}"
                )
                break

            except Exception as exc:
                # Unexpected exception
                last_error_msg = f"UnexpectedError ({exc.__class__.__name__}): {str(exc)}"
                logger.error(
                    f"Unexpected error executing case '{record.id}': {last_error_msg}"
                )
                break

        # Fault isolation fallback: return failed EvaluationResult instead of raising exception
        return EvaluationResult(
            run_id=run_id,
            test_case_id=record.id,
            response=None,
            latency_ms=0.0,
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            error=last_error_msg or "Unknown evaluation error",
        )
