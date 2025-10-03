"""LangGraph adapter for integrating the conscious loop."""

from __future__ import annotations

from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    import langgraph
except ImportError:  # pragma: no cover
    langgraph = None

from ..core.loop import ConsciousLoop, WorkflowResult
from ..core.types import Percept


class LangGraphAdapter:
    """Wraps the loop as a LangGraph-compatible node."""

    def __init__(self, loop: ConsciousLoop) -> None:
        self.loop = loop
        self._last_result: WorkflowResult | None = None

    def ingress(self, content: str, tick: int) -> None:
        percept = Percept(content=content, timestamp=tick)
        self._last_result = self.loop.run_workflow(percept)

    def egress(self) -> Dict[str, Any]:
        if self._last_result is None:
            action = self.loop.act()
        else:
            action = self._last_result.action
        return {"action": action.model_dump(), "tick": self.loop.tick_id}


__all__ = ["LangGraphAdapter"]
