"""Metacognitive metrics utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


def brier_score(pairs: List[Tuple[float, float]]) -> float:
    if not pairs:
        return 0.0
    return sum((pred - actual) ** 2 for pred, actual in pairs) / len(pairs)


def expected_calibration_error(pairs: List[Tuple[float, float]], bins: int = 10) -> float:
    if not pairs:
        return 0.0
    bin_totals = [0.0 for _ in range(bins)]
    bin_counts = [0 for _ in range(bins)]
    bin_actuals = [0.0 for _ in range(bins)]
    for pred, actual in pairs:
        idx = min(bins - 1, int(pred * bins))
        bin_totals[idx] += pred
        bin_actuals[idx] += actual
        bin_counts[idx] += 1
    ece = 0.0
    total = len(pairs)
    for idx in range(bins):
        if bin_counts[idx] == 0:
            continue
        avg_conf = bin_totals[idx] / bin_counts[idx]
        avg_acc = bin_actuals[idx] / bin_counts[idx]
        ece += (bin_counts[idx] / total) * abs(avg_conf - avg_acc)
    return ece


def wrong_at_high_conf(pairs: List[Tuple[float, float]], threshold: float = 0.8) -> float:
    if not pairs:
        return 0.0
    high = [1 for pred, actual in pairs if pred >= threshold and actual < 0.5]
    return sum(high) / max(1, len([1 for pred, _ in pairs if pred >= threshold]))


@dataclass
class MetacogTracker:
    """Accumulates predictions for calibration metrics."""

    observations: List[Tuple[float, float]] = field(default_factory=list)

    def observe(self, predicted: float, actual: float) -> None:
        self.observations.append((max(0.0, min(1.0, predicted)), max(0.0, min(1.0, actual))))

    def metrics(self) -> Dict[str, float]:
        return {
            "brier": brier_score(self.observations),
            "ece": expected_calibration_error(self.observations),
            "wrong_high_conf": wrong_at_high_conf(self.observations),
        }


__all__ = [
    "MetacogTracker",
    "brier_score",
    "expected_calibration_error",
    "wrong_at_high_conf",
]
