"""Typed structures used across the cognitive loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Sequence

from pydantic import BaseModel, Field


class ProcessName(str, Enum):
    """Identifiers for cognitive processes."""

    PERCEPTION = "perception"
    PLANNER = "planner"
    REFLECTOR = "reflector"
    SELF_MODEL = "self_model"
    CRITIC = "critic"


@dataclass(slots=True)
class Percept:
    """External stimulus to the loop."""

    content: str
    modality: str = "text"
    timestamp: int = 0
    salience_hint: float = 0.0


class Coalition(BaseModel):
    """Candidate piece of information competing for broadcast."""

    summary: str
    full_text: str
    salience: float
    source: str
    confidence: float

    @property
    def bounded_salience(self) -> float:
        """Return salience constrained to [0, 1.5] to stabilise dynamics."""

        return max(0.0, min(1.5, self.salience))


class Broadcast(BaseModel):
    """Winning coalition announced in the global workspace."""

    coalition: Coalition
    tick: int


class Action(BaseModel):
    """Observable action chosen by the agent."""

    kind: Literal["say", "tool", "none"] = "none"
    payload: Any = None
    confidence: float = 0.0


@dataclass(slots=True)
class TickTrace:
    """Structured summary of each control loop iteration."""

    tick: int
    broadcast: Optional[Broadcast]
    workspace_state: List[Coalition]
    processes_considered: Dict[ProcessName, List[Coalition]]
    action: Optional[Action]
    metrics: Dict[str, float] = field(default_factory=dict)


class RunConfig(BaseModel):
    """Configuration knobs for a conscious loop run."""

    seed: int = 7
    workspace_capacity: int = 7
    working_memory_items: int = 9
    working_memory_decay: float = 0.15
    workflow_ticks: int = 3
    workflow_narrative_window: int = 5
    episodic_backend: Literal["memory", "sqlite", "duckdb"] = "memory"
    episodic_path: Optional[str] = None
    process_budgets: Dict[ProcessName, int] = Field(default_factory=lambda: {
        ProcessName.PERCEPTION: 512,
        ProcessName.PLANNER: 512,
        ProcessName.REFLECTOR: 384,
        ProcessName.SELF_MODEL: 384,
        ProcessName.CRITIC: 256,
    })
    process_temperature: Dict[ProcessName, float] = Field(default_factory=lambda: {
        ProcessName.PERCEPTION: 0.0,
        ProcessName.PLANNER: 0.1,
        ProcessName.REFLECTOR: 0.2,
        ProcessName.SELF_MODEL: 0.05,
        ProcessName.CRITIC: 0.0,
    })
    anthropomorphism: bool = False
    redaction_rules: Sequence[str] = ("ssn", "password")


__all__ = [
    "Action",
    "Broadcast",
    "Coalition",
    "Percept",
    "ProcessName",
    "RunConfig",
    "TickTrace",
]
