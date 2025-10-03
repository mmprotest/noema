"""Sensor implementations turning environment signals into percepts."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.types import Percept


@dataclass
class TextSensor:
    """Trivial sensor emitting textual percepts."""

    modality: str = "text"

    def sense(self, text: str, tick: int) -> Percept:
        return Percept(content=text, modality=self.modality, timestamp=tick, salience_hint=0.3)


__all__ = ["TextSensor"]
