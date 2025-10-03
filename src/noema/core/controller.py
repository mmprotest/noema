"""Controller orchestrating cognitive processes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, cast

from ..instruments.metacog import MetacogTracker
from ..instruments.narrative import NarrativeStream
from .attention import Attention
from .memory import (
    DuckDBEpisodic,
    EpisodicStore,
    InMemoryEpisodic,
    SqliteEpisodic,
    WorkingMemory,
)
from .processes import Critic, Perception, Planner, Process, Reflector, SelfModel
from .types import Action, Broadcast, Coalition, ProcessName, RunConfig, TickTrace
from .workspace import Workspace


def _episodic_for_config(config: RunConfig) -> EpisodicStore:
    if config.episodic_backend == "sqlite":
        if not config.episodic_path:
            raise ValueError("episodic_path required for sqlite backend")
        return SqliteEpisodic(config.episodic_path)
    if config.episodic_backend == "duckdb":
        if not config.episodic_path:
            raise ValueError("episodic_path required for duckdb backend")
        return DuckDBEpisodic(config.episodic_path)
    return InMemoryEpisodic()


@dataclass
class ControllerState:
    tick: int = 0
    last_broadcast: Optional[Broadcast] = None


class Controller:
    """Coordinates processes within the global workspace loop."""

    def __init__(self, backend, config: RunConfig) -> None:
        self.backend = backend
        self.config = config
        self.workspace = Workspace(capacity=config.workspace_capacity)
        self.working_memory = WorkingMemory(config.working_memory_items, config.working_memory_decay)
        self.episodic = _episodic_for_config(config)
        self.metacog = MetacogTracker()
        self.narrative = NarrativeStream(redactions=config.redaction_rules)
        self.attention = Attention(seed=config.seed)
        self.state = ControllerState()
        self.processes: Dict[ProcessName, Process] = {
            ProcessName.PERCEPTION: Perception(
                backend=self.backend,
                temperature=config.process_temperature[ProcessName.PERCEPTION],
                budget=config.process_budgets[ProcessName.PERCEPTION],
            ),
            ProcessName.PLANNER: Planner(
                backend=self.backend,
                temperature=config.process_temperature[ProcessName.PLANNER],
                budget=config.process_budgets[ProcessName.PLANNER],
            ),
            ProcessName.REFLECTOR: Reflector(
                backend=self.backend,
                temperature=config.process_temperature[ProcessName.REFLECTOR],
                budget=config.process_budgets[ProcessName.REFLECTOR],
            ),
            ProcessName.SELF_MODEL: SelfModel(
                backend=self.backend,
                temperature=config.process_temperature[ProcessName.SELF_MODEL],
                budget=config.process_budgets[ProcessName.SELF_MODEL],
            ),
            ProcessName.CRITIC: Critic(
                backend=self.backend,
                temperature=config.process_temperature[ProcessName.CRITIC],
                budget=config.process_budgets[ProcessName.CRITIC],
            ),
        }

    def perception(self) -> Perception:
        return cast(Perception, self.processes[ProcessName.PERCEPTION])

    def tick(self) -> TickTrace:
        self.state.tick += 1
        proposals: Dict[ProcessName, List[Coalition]] = {}
        all_candidates: List[Coalition] = []
        workspace_state = self.workspace.state()
        last = self.state.last_broadcast

        for name, process in self.processes.items():
            candidate_list = process.propose(workspace_state, self.working_memory, last)
            proposals[name] = candidate_list
            all_candidates.extend(candidate_list)

        if not all_candidates:
            fallback = Coalition(
                summary="Idle",
                full_text="No proposals",
                salience=0.1,
                source="system",
                confidence=0.5,
            )
            all_candidates.append(fallback)

        selected = self.attention.select(all_candidates, workspace_state)
        broadcast = self.workspace.broadcast(selected, tick=self.state.tick)
        self.working_memory.add(selected)
        self.episodic.add(selected)
        for process in self.processes.values():
            process.after_broadcast(broadcast, self.working_memory)

        actual = 1.0 if selected.confidence > 0.5 else 0.0
        self.metacog.observe(selected.confidence, actual)
        self.narrative.append(f"Tick {self.state.tick}: {selected.summary}")

        actions = []
        for process in self.processes.values():
            action = process.act(self.workspace.state(), self.working_memory)
            if action.kind != "none":
                actions.append(action)
        chosen_action = max(actions, key=lambda a: a.confidence, default=Action())

        metrics = self.metacog.metrics()
        metrics_with_actual = {**metrics, "actual": actual}
        trace = TickTrace(
            tick=self.state.tick,
            broadcast=broadcast,
            workspace_state=self.workspace.state(),
            processes_considered=proposals,
            action=chosen_action,
            metrics=metrics_with_actual,
        )
        self.state.last_broadcast = broadcast
        return trace


__all__ = ["Controller", "ControllerState"]
