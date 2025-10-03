"""Minimal deterministic demo using Noema's dummy backend."""

from __future__ import annotations

import json
from pathlib import Path

from noema.core.backends.dummy import DummyBackend
from noema.core.loop import ConsciousLoop
from noema.core.types import RunConfig
from noema.reporting.html_report import save_report
from noema.tasks.evaluations import aggregate_from_traces
from noema.tasks.microworlds import InterruptionCountingTask


def main() -> None:
    """Run a tiny loop, persist a bundle, emit an HTML report, and print metrics."""

    out_dir = Path(__file__).parent / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = out_dir / "hello.run.noema"
    report_path = out_dir / "hello_report.html"

    config = RunConfig()
    backend = DummyBackend(seed=config.seed)
    loop = ConsciousLoop(backend, config)
    env = InterruptionCountingTask(length=12, interruption_rate=0.25, seed=config.seed)

    while True:
        percept = env.next_percept()
        if percept is None:
            break
        loop.ingest(percept)
        loop.tick()

    loop.save_bundle(bundle_path)
    eval_report = aggregate_from_traces(loop.traces, backend=backend)
    save_report(loop.traces, eval_report, report_path)

    metrics = eval_report.metrics
    summary = {
        "brier": round(metrics.get("brier", 0.0), 2),
        "ece": round(metrics.get("ece", 0.0), 2),
        "wrong@high-conf": round(metrics.get("wrong_high_conf", 0.0), 2),
    }
    print(json.dumps(summary, indent=2))
    print(f"Bundle written to {bundle_path}")
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
