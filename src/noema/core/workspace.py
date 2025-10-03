"""Global workspace implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .types import Broadcast, Coalition


@dataclass
class Workspace:
    """Workspace maintains a bounded list of recent coalitions."""

    capacity: int
    _coalitions: List[Coalition] = field(default_factory=list)

    def consider(self, coalition: Coalition) -> None:
        """Insert a coalition keeping the most salient items."""

        self._coalitions.append(coalition)
        self._coalitions.sort(key=lambda c: c.bounded_salience, reverse=True)
        if len(self._coalitions) > self.capacity:
            self._coalitions = self._coalitions[: self.capacity]

    def state(self) -> List[Coalition]:
        """Return current coalitions as an immutable copy."""

        return list(self._coalitions)

    def broadcast(self, coalition: Coalition, tick: int) -> Broadcast:
        """Produce a broadcast event and ensure coalition is present."""

        self.consider(coalition)
        return Broadcast(coalition=coalition, tick=tick)


__all__ = ["Workspace"]
