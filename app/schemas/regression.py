from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RegressionConfig(BaseModel):
    """
    Threshold settings and regression criteria configuration.
    """

    min_pass_rate_pct: Optional[float] = Field(
        default=70.0, description="Minimum acceptable pass rate percentage for candidate."
    )
    max_failure_rate_pct: Optional[float] = Field(
        default=10.0, description="Maximum acceptable failure rate percentage for candidate."
    )
    max_avg_latency_ms: Optional[float] = Field(
        default=2000.0, description="Maximum acceptable average latency in milliseconds."
    )
    max_total_tokens: Optional[int] = Field(
        default=None, description="Maximum allowed total token consumption."
    )
    max_allowed_pass_rate_drop_pct: Optional[float] = Field(
        default=5.0, description="Maximum allowed drop in pass rate compared to baseline."
    )
    max_latency_increase_pct: Optional[float] = Field(
        default=25.0, description="Maximum allowed percentage increase in average latency compared to baseline."
    )
    min_avg_metric_score: Optional[float] = Field(
        default=None, description="Minimum acceptable average metric score across all test cases."
    )


class MetricRegressionViolation(BaseModel):
    """
    Detailed payload describing a specific regression threshold violation.
    """

    metric_name: str = Field(..., description="Name of the evaluated metric or statistic.")
    baseline_value: float = Field(..., description="Baseline value.")
    candidate_value: float = Field(..., description="Candidate value.")
    threshold_rule: str = Field(..., description="The threshold rule description (e.g. 'candidate pass_rate >= 80%').")
    abs_diff: float = Field(..., description="Absolute difference (candidate - baseline).")
    pct_diff: float = Field(..., description="Percentage difference relative to baseline.")
    affected_cases: List[str] = Field(
        default_factory=list, description="List of test case IDs that degraded or failed in candidate."
    )


class RegressionReport(BaseModel):
    """
    Overall regression test evaluation report.
    """

    status: str = Field(..., description="Regression test status: 'PASS' or 'FAIL'.")
    baseline_label: str = Field(..., description="Baseline run/model identifier.")
    candidate_label: str = Field(..., description="Candidate run/model identifier.")
    dataset_version: str = Field(..., description="Benchmark dataset version.")
    total_cases: int = Field(..., description="Total count of evaluated cases.")
    violations: List[MetricRegressionViolation] = Field(
        default_factory=list, description="List of regression violations found."
    )
    summary: str = Field(..., description="Human-readable execution summary.")
