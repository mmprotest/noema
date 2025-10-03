"""High level conscious loop wrapper."""

from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Deque

import yaml

from ..artifacts import bundles
from ..core.backends.base import LLMBackend
from ..tasks.evaluations import EvalReport
from .controller import Controller
from .types import Action, Percept, ProcessName, RunConfig, TickTrace


def _load_config(config: RunConfig | str | Path) -> RunConfig:
    if isinstance(config, RunConfig):
        return config
    path = Path(config)
    data = yaml.safe_load(path.read_text())
    if "process_budgets" in data:
        data["process_budgets"] = {ProcessName(k): v for k, v in data["process_budgets"].items()}
    if "process_temperature" in data:
        data["process_temperature"] = {ProcessName(k): v for k, v in data["process_temperature"].items()}
    return RunConfig.model_validate(data)


class ConsciousLoop:
    """Public API for running the Noema control loop."""

    def __init__(self, backend: LLMBackend, config: RunConfig | str | Path) -> None:
        self.config = _load_config(config)
        self.backend = backend
        self.controller = Controller(backend, self.config)
        self._percepts: Deque[Percept] = deque()
        self.traces: list[TickTrace] = []

    @property
    def tick_id(self) -> int:
        return self.controller.state.tick

    @property
    def seed(self) -> int:
        return self.config.seed

    @property
    def last_broadcast(self):
        return self.controller.state.last_broadcast

    def ingest(self, percept: Percept) -> None:
        self.controller.perception().ingest(percept)
        self._percepts.append(percept)

    def tick(self) -> TickTrace:
        trace = self.controller.tick()
        self.traces.append(trace)
        return trace

    def act(self) -> Action:
        if not self.traces:
            return Action()
        return self.traces[-1].action or Action()

    def eval(self) -> EvalReport:
        from ..tasks.evaluations import aggregate_from_traces

        return aggregate_from_traces(self.traces)

    def save_bundle(self, path: str | Path) -> str:
        return bundles.create_bundle(path, self)


__all__ = ["ConsciousLoop"]
