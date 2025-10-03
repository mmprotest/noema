"""Run the interruption task and print evaluation summary."""

from __future__ import annotations

from ..core.backends.dummy import DummyBackend
from ..core.loop import ConsciousLoop
from ..core.types import Percept, RunConfig
from ..tasks.microworlds import InterruptionCountingTask


def main() -> None:
    config = RunConfig()
    loop = ConsciousLoop(DummyBackend(seed=config.seed), config)
    env = InterruptionCountingTask(length=30, interruption_rate=0.3)
    while True:
        percept = env.next_percept()
        if percept is None:
            break
        result = loop.run_workflow(percept)
        env.apply_action(result.action)
    report = loop.eval()
    print("Interruption demo metrics:")
    for key, value in report.metrics.items():
        print(f"  {key}: {value:.3f}")


if __name__ == "__main__":
    main()
