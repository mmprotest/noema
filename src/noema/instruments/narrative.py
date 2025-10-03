"""Narrative stream for compact run summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass
class NarrativeStream:
    """Maintains a rolling log of textual summaries."""

    redactions: Iterable[str]
    entries: List[str] = field(default_factory=list)

    def append(self, line: str) -> None:
        clean = line
        for token in self.redactions:
            clean = clean.replace(token, "[redacted]")
        self.entries.append(clean[:400])

    def last(self, n: int = 5) -> List[str]:
        return self.entries[-n:]


__all__ = ["NarrativeStream"]
