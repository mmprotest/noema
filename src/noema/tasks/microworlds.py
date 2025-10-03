"""Deterministic microworld tasks feeding percepts to the loop."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional

from ..core.types import Action, Percept


@dataclass
class InterruptionCountingTask:
    """Simple counting task with random interruptions."""

    length: int
    interruption_rate: float = 0.2
    seed: int = 7
    index: int = 0
    interruptions: List[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        rng = random.Random(self.seed)
        self.interruptions = [i for i in range(self.length) if rng.random() < self.interruption_rate]

    def next_percept(self) -> Optional[Percept]:
        if self.index >= self.length:
            return None
        content = f"Count {self.index}"
        if self.index in self.interruptions:
            content += " -- interruption"
        percept = Percept(content=content, timestamp=self.index, salience_hint=0.4)
        self.index += 1
        return percept

    def apply_action(self, action: Action) -> None:
        pass


@dataclass
class NBackTask:
    """Working memory span test."""

    n: int
    length: int
    seed: int = 11
    sequence: List[str] = field(default_factory=list)
    index: int = 0

    def __post_init__(self) -> None:
        rng = random.Random(self.seed)
        alphabet = ["A", "B", "C", "D"]
        self.sequence = [rng.choice(alphabet) for _ in range(self.length)]

    def next_percept(self) -> Optional[Percept]:
        if self.index >= self.length:
            return None
        char = self.sequence[self.index]
        target = self.sequence[self.index - self.n] if self.index >= self.n else "?"
        content = f"Stimulus {char}; target {target}"
        percept = Percept(content=content, timestamp=self.index, salience_hint=0.3)
        self.index += 1
        return percept

    def apply_action(self, action: Action) -> None:
        pass


@dataclass
class ChangeBlindnessTask:
    """Task requiring noticing changes across scenes."""

    scenes: List[str]
    seed: int = 13
    index: int = 0

    def next_percept(self) -> Optional[Percept]:
        if self.index >= len(self.scenes):
            return None
        content = self.scenes[self.index]
        percept = Percept(content=content, timestamp=self.index, salience_hint=0.5)
        self.index += 1
        return percept

    def apply_action(self, action: Action) -> None:
        pass


__all__ = [
    "InterruptionCountingTask",
    "NBackTask",
    "ChangeBlindnessTask",
]
