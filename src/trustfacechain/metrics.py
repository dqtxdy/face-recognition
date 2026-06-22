"""Biometric verification metrics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Confusion:
    threshold: float
    true_accepts: int
    false_accepts: int
    true_rejects: int
    false_rejects: int

    @property
    def far(self) -> float:
        impostor_total = self.false_accepts + self.true_rejects
        return self.false_accepts / impostor_total if impostor_total else 0.0

    @property
    def frr(self) -> float:
        genuine_total = self.true_accepts + self.false_rejects
        return self.false_rejects / genuine_total if genuine_total else 0.0

    @property
    def tar(self) -> float:
        return 1.0 - self.frr

    @property
    def accuracy(self) -> float:
        total = (
            self.true_accepts
            + self.false_accepts
            + self.true_rejects
            + self.false_rejects
        )
        correct = self.true_accepts + self.true_rejects
        return correct / total if total else 0.0

    @property
    def recall(self) -> float:
        return self.tar

    @property
    def precision(self) -> float:
        predicted_positives = self.true_accepts + self.false_accepts
        return self.true_accepts / predicted_positives if predicted_positives else 0.0

    @property
    def f1_score(self) -> float:
        prec = self.precision
        rec = self.recall
        return 2.0 * (prec * rec) / (prec + rec) if (prec + rec) > 0.0 else 0.0


@dataclass(frozen=True)
class VerificationReport:
    best_threshold: float
    best_accuracy: float
    eer: float
    eer_threshold: float
    auc: float
    best_precision: float
    best_recall: float
    best_f1_score: float
    operating_points: list[Confusion]

    def to_dict(self) -> dict[str, object]:
        return {
            "best_threshold": self.best_threshold,
            "best_accuracy": self.best_accuracy,
            "eer": self.eer,
            "eer_threshold": self.eer_threshold,
            "auc": self.auc,
            "best_precision": self.best_precision,
            "best_recall": self.best_recall,
            "best_f1_score": self.best_f1_score,
            "operating_points": [
                {
                    "threshold": point.threshold,
                    "accuracy": point.accuracy,
                    "far": point.far,
                    "frr": point.frr,
                    "tar": point.tar,
                    "precision": point.precision,
                    "recall": point.recall,
                    "f1_score": point.f1_score,
                    "true_accepts": point.true_accepts,
                    "false_accepts": point.false_accepts,
                    "true_rejects": point.true_rejects,
                    "false_rejects": point.false_rejects,
                }
                for point in self.operating_points
            ],
        }


def confusion_at_threshold(
    *,
    scores: list[float],
    labels: list[int],
    threshold: float,
) -> Confusion:
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have the same length")

    true_accepts = false_accepts = true_rejects = false_rejects = 0
    for score, label in zip(scores, labels, strict=True):
        accepted = score >= threshold
        genuine = label == 1
        if accepted and genuine:
            true_accepts += 1
        elif accepted and not genuine:
            false_accepts += 1
        elif not accepted and genuine:
            false_rejects += 1
        else:
            true_rejects += 1

    return Confusion(
        threshold=threshold,
        true_accepts=true_accepts,
        false_accepts=false_accepts,
        true_rejects=true_rejects,
        false_rejects=false_rejects,
    )


def candidate_thresholds(scores: list[float]) -> list[float]:
    if not scores:
        return [0.0]
    values = sorted(set(scores))
    thresholds = [values[0] - 1e-9]
    thresholds.extend((left + right) / 2 for left, right in zip(values, values[1:]))
    thresholds.append(values[-1] + 1e-9)
    return thresholds


def calculate_auc(points: list[Confusion]) -> float:
    """Compute Area Under the ROC Curve (AUC) using the trapezoidal rule."""
    # Extract (far, tar) pairs
    xy = [(p.far, p.tar) for p in points]
    # Sort by FAR (False Acceptance Rate) ascending, and then by TAR ascending to ensure stable integration
    xy = sorted(xy, key=lambda p: (p[0], p[1]))

    auc = 0.0
    for i in range(len(xy) - 1):
        x1, y1 = xy[i]
        x2, y2 = xy[i + 1]
        auc += 0.5 * (y1 + y2) * (x2 - x1)
    return auc


def evaluate_scores(*, scores: list[float], labels: list[int]) -> VerificationReport:
    points = [
        confusion_at_threshold(scores=scores, labels=labels, threshold=threshold)
        for threshold in candidate_thresholds(scores)
    ]
    best = max(points, key=lambda point: (point.accuracy, -abs(point.far - point.frr)))
    eer_point = min(points, key=lambda point: abs(point.far - point.frr))
    eer = (eer_point.far + eer_point.frr) / 2
    auc = calculate_auc(points)
    return VerificationReport(
        best_threshold=best.threshold,
        best_accuracy=best.accuracy,
        eer=eer,
        eer_threshold=eer_point.threshold,
        auc=auc,
        best_precision=best.precision,
        best_recall=best.recall,
        best_f1_score=best.f1_score,
        operating_points=points,
    )

