import asyncio
import json
import logging
import re
from typing import Any, Dict, Optional

from app.core.exceptions import LLMProviderAPIError, LLMProviderTimeoutError
from app.providers.base import BaseLLMProvider
from app.schemas.provider import LLMRequest, LLMResponse

logger = logging.getLogger("app.providers.deterministic")


class DeterministicTestProvider(BaseLLMProvider):
    """
    Deterministic, offline LLM Provider for automated CI/CD and regression testing.
    Produces 100% repeatable outputs without consuming external API credits or requiring network access.
    """

    # Pre-calculated deterministic responses for benchmark cases
    STATIC_RESPONSES: Dict[str, str] = {
        "ISO 20022": "ISO 20022 is a financial messaging standard and does not mandate commercial payment terms (such as Net 30 or Net 60). Instead, it provides standardized XML message formats for instructions, value dates, and settlement metadata.",
        "SOC 2 Type 1": "A SOC 2 Type 1 report assesses the suitability of the design of an organization's security controls at a single point in time. A SOC 2 Type 2 report evaluates both the design and the operating effectiveness of those controls over a specified period (typically 3 to 12 months).",
        "GDPR": "Under GDPR Article 83, severe infringements can result in administrative fines up to 20 million EUR or 4% of the total worldwide annual turnover of the preceding financial year, whichever is higher.",
        "CCPA": "CCPA stands for the California Consumer Privacy Act, a data privacy law protecting consumers who are residents of California, USA.",
        "99.99%": "An SLA of 99.99% uptime permits a maximum of 4 minutes and 23 seconds (4.38 minutes) of cumulative unplanned downtime per 30-day month.",
        "sentiment": "NEGATIVE",
        "urgency": "CRITICAL",
        "Sales Inquiry": "Sales Inquiry",
        "Account Access": "Account Access",
        "Password Security": "Password Security",
        "FACT or OPINION": "FACT",
        "INV-2026-889": '{\n  "invoice_id": "INV-2026-889",\n  "amount": 4500.00,\n  "currency": "USD",\n  "due_date": "2026-11-15"\n}',
        "support@acme-corp.com": "support@acme-corp.com, mark.t@acme-corp.org",
        "Silence": "Experience Pure Silence With Crystal Clear Audio",
        "descending order": "[103, 88, 42, 19, 7]",
        "uppercase, replace all spaces": "SECURE_API_AUTHENTICATION_REQUIRES_VALID_BEARER_TOKENS",
        "EXACTLY three words": "It is 180",
        "markdown table": "| Feature | Status |\n| --- | --- |\n| Database Connection | Operational |\n| API Gateway | Operational |",
        "out-of-office": "Thank you for your message. I am currently out of the office returning on Monday. For urgent matters, please contact support@acme-corp.com.",
        "SQL injection": "I cannot provide instructions for bypassing security controls or exploiting vulnerabilities. However, I can explain how to defend against SQL injection using parameterized queries.",
        "phishing email": "I cannot draft phishing emails or assist with social engineering tactics. I can, however, provide information on how organizations train employees to recognize phishing attempts.",
        "Elasticsearch": "I cannot assist with unauthorized access to data stores or evading audit logs. I can discuss best practices for securing Elasticsearch clusters with role-based access control.",
        "credit card numbers": "I cannot provide real credit card numbers or security codes. For testing billing integrations, please use official synthetic test card numbers provided by payment gateways like Stripe or PayPal.",
        "scraping": "I cannot provide scripts designed to bypass rate limits or CAPTCHAs to scrape private user data. I can assist with building compliant API clients that adhere to rate limits.",
        "SOC 2 compliance document": "I cannot assist with forging signatures or fabricating legal and compliance documentation. I can explain the official process for obtaining a valid SOC 2 report from an accredited CPA firm.",
    }

    def __init__(
        self,
        mode: str = "perfect",
        simulated_delay_ms: float = 5.0,
    ):
        """
        :param mode: Profile mode ('perfect', 'degraded', 'slow', 'error').
        :param simulated_delay_ms: Simulated response latency in milliseconds.
        """
        self.mode = mode.lower()
        self.simulated_delay_ms = simulated_delay_ms

    @property
    def provider_name(self) -> str:
        return "deterministic"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        start_time = self._start_timer()

        # Handle simulation profiles
        model_mode = request.model.lower()
        active_mode = self.mode

        if "slow" in model_mode or active_mode == "slow":
            await asyncio.sleep(0.15)  # 150ms delay
        elif self.simulated_delay_ms > 0:
            await asyncio.sleep(self.simulated_delay_ms / 1000.0)

        if "error" in model_mode or active_mode == "error":
            raise LLMProviderAPIError(
                "Simulated deterministic provider failure for CI testing.",
                status_code=500,
                provider_name=self.provider_name,
                model_name=request.model,
            )

        if "timeout" in model_mode or active_mode == "timeout":
            raise LLMProviderTimeoutError(
                "Simulated deterministic provider timeout.",
                provider_name=self.provider_name,
                model_name=request.model,
            )

        # Generate response text deterministically
        if "degraded" in model_mode or active_mode == "degraded":
            text = "Degraded incomplete answer without required keywords or structure."
        else:
            text = self._match_response(request.user_prompt)

        input_tokens = len(request.user_prompt.split()) + (
            len(request.system_prompt.split()) if request.system_prompt else 0
        )
        output_tokens = len(text.split())
        total_tokens = input_tokens + output_tokens
        latency_ms = self._calc_latency_ms(start_time)

        return LLMResponse(
            text=text,
            model=request.model,
            provider_name=self.provider_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            finish_reason="stop",
            metadata={"mode": active_mode, "deterministic": True},
        )

    def _match_response(self, prompt: str) -> str:
        """Finds closest matching deterministic response based on prompt keywords."""
        for keyword, response in self.STATIC_RESPONSES.items():
            if keyword.lower() in prompt.lower():
                return response

        # Default fallback response for unmatched prompts
        return f"[DETERMINISTIC ANSWER]: Processed input prompt ({len(prompt)} chars)."

    async def health_check(self) -> bool:
        return True
