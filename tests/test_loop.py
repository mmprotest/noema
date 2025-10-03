from __future__ import annotations

from noema.core.backends.dummy import DummyBackend
from noema.core.loop import ConsciousLoop, WorkflowResult
from noema.core.types import Percept, RunConfig


def _run_loop(seed: int) -> list[str]:
    config = RunConfig(seed=seed)
    loop = ConsciousLoop(DummyBackend(seed=config.seed), config)
    for tick in range(5):
        loop.ingest(Percept(content=f"stimulus {tick}", timestamp=tick, salience_hint=0.4))
        loop.tick()
    return [trace.broadcast.coalition.summary for trace in loop.traces if trace.broadcast]


def test_tick_advances_and_memory_bounds() -> None:
    config = RunConfig(seed=2, working_memory_items=3)
    loop = ConsciousLoop(DummyBackend(seed=config.seed), config)
    for idx in range(6):
        loop.ingest(Percept(content=f"item {idx}", timestamp=idx, salience_hint=0.5))
        trace = loop.tick()
    assert loop.tick_id == 6
    assert trace.broadcast is not None
    assert len(loop.controller.working_memory.contents()) <= config.working_memory_items


def test_deterministic_traces() -> None:
    traces_a = _run_loop(7)
    traces_b = _run_loop(7)
    assert traces_a == traces_b


def test_run_workflow_batches_ticks() -> None:
    config = RunConfig(seed=3, workflow_ticks=2)
    loop = ConsciousLoop(DummyBackend(seed=config.seed), config)
    result = loop.run_workflow(Percept(content="hello", timestamp=1, salience_hint=0.5))
    assert isinstance(result, WorkflowResult)
    assert len(result.percepts) == 1
    assert len(result.traces) == config.workflow_ticks
    assert loop.tick_id == config.workflow_ticks


def test_run_workflow_consumes_pending_percepts() -> None:
    config = RunConfig(seed=4, workflow_ticks=1)
    loop = ConsciousLoop(DummyBackend(seed=config.seed), config)
    loop.ingest(Percept(content="first", timestamp=1, salience_hint=0.3))
    loop.ingest(Percept(content="second", timestamp=2, salience_hint=0.7))
    assert len(loop.pending_percepts()) == 2
    result = loop.run_workflow()
    assert len(result.percepts) == 2
    assert loop.pending_percepts() == []
    assert len(result.traces) >= 2
