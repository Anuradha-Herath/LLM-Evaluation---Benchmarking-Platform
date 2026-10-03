import logging
from typing import Dict, List, Optional

from app.evaluators.metrics.base import MetricResult
from app.evaluators.result import EvaluationRunSummary
from app.schemas.regression import (
    MetricRegressionViolation,
    RegressionConfig,
    RegressionReport,
)

logger = logging.getLogger("app.services.regression_service")


class RegressionService:
    """
    Evaluates Candidate run outputs against Baseline runs based on configurable regression thresholds.
    """

    @classmethod
    def evaluate_regression(
        cls,
        baseline_summary: EvaluationRunSummary,
        candidate_summary: EvaluationRunSummary,
        baseline_metric_map: Optional[Dict[str, List[MetricResult]]] = None,
        candidate_metric_map: Optional[Dict[str, List[MetricResult]]] = None,
        config: Optional[RegressionConfig] = None,
        baseline_label: str = "Baseline",
        candidate_label: str = "Candidate",
    ) -> RegressionReport:
        """
        Compares candidate evaluation run against baseline evaluation run.

        :return: RegressionReport containing PASS/FAIL status, metrics diffs, and violations.
        """
        cfg = config or RegressionConfig()
        violations: List[MetricRegressionViolation] = []

        base_run = baseline_summary.run
        cand_run = candidate_summary.run

        # 1. Compute summary statistics for baseline & candidate
        base_total = base_run.total_cases
        cand_total = cand_run.total_cases

        if candidate_metric_map and len(candidate_metric_map) > 0:
            cand_passed = sum(1 for cid, mlist in candidate_metric_map.items() if mlist and all(m.passed for m in mlist))
            cand_failed = cand_total - cand_passed
        else:
            cand_passed = cand_run.passed_cases
            cand_failed = cand_run.failed_cases

        if baseline_metric_map and len(baseline_metric_map) > 0:
            base_passed = sum(1 for cid, mlist in baseline_metric_map.items() if mlist and all(m.passed for m in mlist))
        else:
            base_passed = base_run.passed_cases

        base_pass_rate = round((base_passed / base_total) * 100.0, 2) if base_total > 0 else 0.0
        cand_pass_rate = round((cand_passed / cand_total) * 100.0, 2) if cand_total > 0 else 0.0
        cand_fail_rate = round((cand_failed / cand_total) * 100.0, 2) if cand_total > 0 else 0.0

        base_lat = baseline_summary.avg_latency_ms
        cand_lat = candidate_summary.avg_latency_ms

        base_tokens = baseline_summary.total_tokens
        cand_tokens = candidate_summary.total_tokens

        # 2. Identify itemized affected cases (cases that passed in baseline but failed in candidate)
        base_results_map = {r.test_case_id: r for r in baseline_summary.results}
        cand_results_map = {r.test_case_id: r for r in candidate_summary.results}

        affected_cases = []
        for case_id in base_results_map.keys():
            cand_res = cand_results_map.get(case_id)
            if candidate_metric_map:
                cand_m = candidate_metric_map.get(case_id, [])
                base_m = (baseline_metric_map or {}).get(case_id, [])
                base_ok = base_m and all(m.passed for m in base_m)
                cand_ok = cand_m and all(m.passed for m in cand_m)
            else:
                base_res = base_results_map[case_id]
                base_ok = base_res.error is None
                cand_ok = cand_res and cand_res.error is None

            if base_ok and not cand_ok:
                affected_cases.append(case_id)


        # 3. Assert Threshold Rules

        # Rule 1: Candidate Minimum Pass Rate (%)
        if cfg.min_pass_rate_pct is not None and cand_pass_rate < cfg.min_pass_rate_pct:
            abs_diff = round(cand_pass_rate - base_pass_rate, 2)
            pct_diff = round(((cand_pass_rate - base_pass_rate) / base_pass_rate) * 100.0, 2) if base_pass_rate > 0 else 0.0
            violations.append(
                MetricRegressionViolation(
                    metric_name="pass_rate_pct",
                    baseline_value=base_pass_rate,
                    candidate_value=cand_pass_rate,
                    threshold_rule=f"candidate pass_rate ({cand_pass_rate:.1f}%) >= min_pass_rate ({cfg.min_pass_rate_pct:.1f}%)",
                    abs_diff=abs_diff,
                    pct_diff=pct_diff,
                    affected_cases=affected_cases,
                )
            )

        # Rule 2: Pass Rate Drop (%) relative to Baseline
        pass_rate_drop = round(base_pass_rate - cand_pass_rate, 2)
        if (
            cfg.max_allowed_pass_rate_drop_pct is not None
            and pass_rate_drop > cfg.max_allowed_pass_rate_drop_pct
        ):
            violations.append(
                MetricRegressionViolation(
                    metric_name="pass_rate_drop_pct",
                    baseline_value=base_pass_rate,
                    candidate_value=cand_pass_rate,
                    threshold_rule=f"pass_rate_drop ({pass_rate_drop:.1f}%) <= max_allowed_drop ({cfg.max_allowed_pass_rate_drop_pct:.1f}%)",
                    abs_diff=-pass_rate_drop,
                    pct_diff=round((-pass_rate_drop / base_pass_rate) * 100.0, 2) if base_pass_rate > 0 else 0.0,
                    affected_cases=affected_cases,
                )
            )

        # Rule 3: Candidate Maximum Failure Rate (%)
        if cfg.max_failure_rate_pct is not None and cand_fail_rate > cfg.max_failure_rate_pct:
            base_fail_rate = round((base_run.failed_cases / base_total) * 100.0, 2) if base_total > 0 else 0.0
            violations.append(
                MetricRegressionViolation(
                    metric_name="failure_rate_pct",
                    baseline_value=base_fail_rate,
                    candidate_value=cand_fail_rate,
                    threshold_rule=f"candidate failure_rate ({cand_fail_rate:.1f}%) <= max_failure_rate ({cfg.max_failure_rate_pct:.1f}%)",
                    abs_diff=round(cand_fail_rate - base_fail_rate, 2),
                    pct_diff=round(((cand_fail_rate - base_fail_rate) / base_fail_rate) * 100.0, 2) if base_fail_rate > 0 else 0.0,
                    affected_cases=affected_cases,
                )
            )

        # Rule 4: Maximum Average Latency (ms)
        if cfg.max_avg_latency_ms is not None and cand_lat > cfg.max_avg_latency_ms:
            abs_diff = round(cand_lat - base_lat, 2)
            pct_diff = round(((cand_lat - base_lat) / base_lat) * 100.0, 2) if base_lat > 0 else 0.0
            violations.append(
                MetricRegressionViolation(
                    metric_name="avg_latency_ms",
                    baseline_value=base_lat,
                    candidate_value=cand_lat,
                    threshold_rule=f"candidate avg_latency ({cand_lat:.1f} ms) <= max_allowed ({cfg.max_avg_latency_ms:.1f} ms)",
                    abs_diff=abs_diff,
                    pct_diff=pct_diff,
                    affected_cases=[],
                )
            )

        # Rule 5: Latency Percentage Increase (%)
        if base_lat > 0:
            lat_inc_pct = round(((cand_lat - base_lat) / base_lat) * 100.0, 2)
            if (
                cfg.max_latency_increase_pct is not None
                and lat_inc_pct > cfg.max_latency_increase_pct
            ):
                violations.append(
                    MetricRegressionViolation(
                        metric_name="latency_increase_pct",
                        baseline_value=base_lat,
                        candidate_value=cand_lat,
                        threshold_rule=f"latency increase ({lat_inc_pct:.1f}%) <= max_allowed_increase ({cfg.max_latency_increase_pct:.1f}%)",
                        abs_diff=round(cand_lat - base_lat, 2),
                        pct_diff=lat_inc_pct,
                        affected_cases=[],
                    )
                )

        # Rule 6: Maximum Total Token Usage
        if cfg.max_total_tokens is not None and cand_tokens > cfg.max_total_tokens:
            abs_diff = cand_tokens - base_tokens
            pct_diff = round(((cand_tokens - base_tokens) / base_tokens) * 100.0, 2) if base_tokens > 0 else 0.0
            violations.append(
                MetricRegressionViolation(
                    metric_name="total_tokens",
                    baseline_value=float(base_tokens),
                    candidate_value=float(cand_tokens),
                    threshold_rule=f"candidate total_tokens ({cand_tokens}) <= max_allowed ({cfg.max_total_tokens})",
                    abs_diff=float(abs_diff),
                    pct_diff=pct_diff,
                    affected_cases=[],
                )
            )

        # Rule 7: Minimum Average Metric Quality / Accuracy Score
        if candidate_metric_map and cfg.min_avg_metric_score is not None:
            cand_scores = [
                m.score for metrics in candidate_metric_map.values() for m in metrics if m.score is not None
            ]
            base_scores = [
                m.score for metrics in (baseline_metric_map or {}).values() for m in metrics if m.score is not None
            ]
            cand_avg_score = round(sum(cand_scores) / len(cand_scores), 4) if cand_scores else 1.0
            base_avg_score = round(sum(base_scores) / len(base_scores), 4) if base_scores else 1.0

            if cand_avg_score < cfg.min_avg_metric_score:
                abs_diff = round(cand_avg_score - base_avg_score, 4)
                pct_diff = round(((cand_avg_score - base_avg_score) / base_avg_score) * 100.0, 2) if base_avg_score > 0 else 0.0

                cand_case_score = {
                    cid: sum(m.score for m in mlist) / len(mlist) if mlist else 0.0
                    for cid, mlist in candidate_metric_map.items()
                }
                base_case_score = {
                    cid: sum(m.score for m in mlist) / len(mlist) if mlist else 0.0
                    for cid, mlist in (baseline_metric_map or {}).items()
                }
                metric_affected = [
                    cid for cid, c_score in cand_case_score.items()
                    if c_score < base_case_score.get(cid, 1.0)
                ]

                violations.append(
                    MetricRegressionViolation(
                        metric_name="avg_quality_score",
                        baseline_value=base_avg_score,
                        candidate_value=cand_avg_score,
                        threshold_rule=f"candidate avg quality score ({cand_avg_score:.2f}) >= min_avg_metric_score ({cfg.min_avg_metric_score:.2f})",
                        abs_diff=abs_diff,
                        pct_diff=pct_diff,
                        affected_cases=metric_affected,
                    )
                )

        status = "PASS" if len(violations) == 0 else "FAIL"
        summary_msg = (
            f"Regression evaluation passed cleanly with 0 violations."
            if status == "PASS"
            else f"Regression evaluation FAILED with {len(violations)} threshold violation(s)."
        )

        return RegressionReport(
            status=status,
            baseline_label=baseline_label,
            candidate_label=candidate_label,
            dataset_version=cand_run.dataset_version,
            total_cases=cand_total,
            violations=violations,
            summary=summary_msg,
        )
