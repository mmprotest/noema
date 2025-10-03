"""LangGraph adapter for integrating the conscious loop."""

from __future__ import annotations

from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    import langgraph
except ImportError:  # pragma: no cover
    langgraph = None

from ..core.loop import ConsciousLoop
from ..core.types import Action, Percept


class LangGraphAdapter:
    """Wraps the loop as a LangGraph-compatible node."""

    def __init__(self, loop: ConsciousLoop) -> None:
        self.loop = loop

    def ingress(self, content: str, tick: int) -> None:
        percept = Percept(content=content, timestamp=tick)
        self.loop.ingest(percept)
        self.loop.tick()

    def egress(self) -> Dict[str, Any]:
        action = self.loop.act()
        return {"action": action.model_dump(), "tick": self.loop.tick_id}


__all__ = ["LangGraphAdapter"]
