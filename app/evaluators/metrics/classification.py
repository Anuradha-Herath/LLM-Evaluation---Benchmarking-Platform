from typing import Any, Dict, List, Optional
from app.evaluators.metrics.base import BaseMetric, MetricResult


class ClassificationMetric(BaseMetric):
    """
    Evaluates classification outputs against target labels, computing Accuracy, Precision, Recall, and F1 scores.
    """

    @property
    def name(self) -> str:
        return "classification_metrics"

    @property
    def version(self) -> str:
        return "1.0.0"

    def _clean_label(self, label: str) -> str:
        if not label:
            return ""
        return label.strip().upper().strip("[]().'\"")

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
                reasoning="No reference target label provided for classification evaluation.",
            )

        pred = self._clean_label(response_text)
        target = self._clean_label(reference_answer)

        # For single sample evaluation:
        # Match yields Precision=1, Recall=1, F1=1, Accuracy=1
        matched = (pred == target) or (target in pred)
        score = 1.0 if matched else 0.0

        return MetricResult(
            metric_name=self.name,
            metric_version=self.version,
            score=score,
            passed=matched,
            reasoning=f"Predicted label '{pred}' matched target '{target}'."
            if matched
            else f"Predicted label '{pred}' failed to match target '{target}'.",
            metadata={
                "predicted_label": pred,
                "target_label": target,
                "accuracy": score,
                "precision": score,
                "recall": score,
                "f1_score": score,
            },
        )

    @classmethod
    def compute_batch_metrics(
        cls, predictions: List[str], references: List[str]
    ) -> Dict[str, float]:
        """
        Calculates aggregate multi-class Accuracy, Precision, Recall, and F1 across a dataset run.

        :param predictions: List of predicted label strings.
        :param references: List of ground-truth reference label strings.
        :return: Dictionary containing aggregate classification metrics.
        """
        if not predictions or len(predictions) != len(references):
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

        cleaned_preds = [p.strip().upper().strip("[]().'\"") for p in predictions]
        cleaned_refs = [r.strip().upper().strip("[]().'\"") for r in references]

        labels = sorted(list(set(cleaned_refs + cleaned_preds)))
        total = len(cleaned_refs)
        correct = sum(1 for p, r in zip(cleaned_preds, cleaned_refs) if p == r)
        accuracy = round(correct / total, 4) if total > 0 else 0.0

        # Calculate Macro Precision, Recall, F1
        precisions = []
        recalls = []
        f1s = []

        for label in labels:
            tp = sum(1 for p, r in zip(cleaned_preds, cleaned_refs) if p == label and r == label)
            fp = sum(1 for p, r in zip(cleaned_preds, cleaned_refs) if p == label and r != label)
            fn = sum(1 for p, r in zip(cleaned_preds, cleaned_refs) if p != label and r == label)

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

            precisions.append(prec)
            recalls.append(rec)
            f1s.append(f1)

        macro_precision = round(sum(precisions) / len(labels), 4) if labels else 0.0
        macro_recall = round(sum(recalls) / len(labels), 4) if labels else 0.0
        macro_f1 = round(sum(f1s) / len(labels), 4) if labels else 0.0

        return {
            "accuracy": accuracy,
            "precision": macro_precision,
            "recall": macro_recall,
            "f1": macro_f1,
            "total_samples": total,
        }
