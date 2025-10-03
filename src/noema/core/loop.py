"""High level conscious loop wrapper."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Deque, Iterable, List

import yaml

from ..artifacts import bundles
from ..core.backends.base import LLMBackend
from ..tasks.evaluations import EvalReport
from .controller import Controller
from .types import Action, Broadcast, Percept, ProcessName, RunConfig, TickTrace


@dataclass(slots=True)
class WorkflowResult:
    """Structured summary for a complete consciousness workflow run."""

    percepts: List[Percept] = field(default_factory=list)
    traces: List[TickTrace] = field(default_factory=list)
    action: Action = field(default_factory=Action)
    narrative: List[str] = field(default_factory=list)

    def broadcasts(self) -> Iterable[Broadcast]:
        """Yield broadcast events from the workflow in order."""

        for trace in self.traces:
            if trace.broadcast:
                yield trace.broadcast

    def last_broadcast(self) -> Broadcast | None:
        """Return the most recent broadcast event if available."""

        for trace in reversed(self.traces):
            if trace.broadcast:
                return trace.broadcast
        return None


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

    def pending_percepts(self) -> list[Percept]:
        """Return percepts awaiting processing by the workflow."""

        return list(self._percepts)

    def tick(self) -> TickTrace:
        trace = self.controller.tick()
        self.traces.append(trace)
        return trace

    def run_workflow(
        self,
        percept: Percept | None = None,
        *,
        ticks: int | None = None,
    ) -> WorkflowResult:
        """Execute a full perceive-think-act workflow cycle.

        Parameters
        ----------
        percept:
            Optional percept to ingest before starting the workflow.
        ticks:
            Override for how many controller ticks to execute. Defaults to
            ``config.workflow_ticks`` with at least one tick per pending percept.
        """

        if percept is not None:
            self.ingest(percept)

        pending: list[Percept] = list(self._percepts)
        self._percepts.clear()

        planned_ticks = ticks if ticks is not None else self.config.workflow_ticks
        planned_ticks = max(planned_ticks, len(pending))
        planned_ticks = max(planned_ticks, 1)

        traces: list[TickTrace] = []
        actions: list[Action] = []

        for _ in range(planned_ticks):
            trace = self.tick()
            traces.append(trace)
            if trace.action and trace.action.kind != "none":
                actions.append(trace.action)

        chosen = max(actions, key=lambda action: action.confidence, default=Action())
        narrative = self.controller.narrative.last(self.config.workflow_narrative_window)

        return WorkflowResult(
            percepts=pending,
            traces=traces,
            action=chosen,
            narrative=narrative,
        )

    def act(self) -> Action:
        if not self.traces:
            return Action()
        return self.traces[-1].action or Action()

    def eval(self) -> EvalReport:
        from ..tasks.evaluations import aggregate_from_traces

        return aggregate_from_traces(self.traces)

    def save_bundle(self, path: str | Path) -> str:
        return bundles.create_bundle(path, self)


__all__ = ["ConsciousLoop", "WorkflowResult"]
