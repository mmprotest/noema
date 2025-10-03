from __future__ import annotations

from noema.core.backends.dummy import DummyBackend
from noema.core.loop import ConsciousLoop
from noema.core.types import Percept, RunConfig
from noema.tasks.evaluations import aggregate_from_traces


def test_evaluation_metrics_are_bounded() -> None:
    config = RunConfig(seed=5)
    loop = ConsciousLoop(DummyBackend(seed=config.seed), config)
    for tick in range(10):
        loop.run_workflow(Percept(content=f"tick {tick}", timestamp=tick, salience_hint=0.4))
    report = aggregate_from_traces(loop.traces)
    assert set(report.metrics.keys()) >= {
        "interruption_recovery",
        "self_reference",
        "wm_span",
        "brier",
        "ece",
        "wrong_high_conf",
        "narrative_coherence",
    }
    for value in report.metrics.values():
        assert 0.0 <= value <= 5.0
