from __future__ import annotations

from noema.instruments.metacog import (
    MetacogTracker,
    brier_score,
    expected_calibration_error,
    wrong_at_high_conf,
)


def test_brier_and_ece() -> None:
    pairs = [(0.9, 1.0), (0.2, 0.0), (0.5, 1.0)]
    assert 0.0 <= brier_score(pairs) <= 1.0
    assert 0.0 <= expected_calibration_error(pairs) <= 1.0


def test_tracker_accumulates() -> None:
    tracker = MetacogTracker()
    tracker.observe(0.9, 1.0)
    tracker.observe(0.2, 0.0)
    metrics = tracker.metrics()
    assert set(metrics.keys()) == {"brier", "ece", "wrong_high_conf"}
    assert metrics["wrong_high_conf"] == wrong_at_high_conf([(0.9, 1.0), (0.2, 0.0)])
