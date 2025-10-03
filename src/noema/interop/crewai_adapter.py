"""CrewAI adapter stub."""

from __future__ import annotations

from typing import Any, Dict

try:  # pragma: no cover
    import crewai
except ImportError:  # pragma: no cover
    crewai = None

from ..core.loop import ConsciousLoop
from ..core.types import Percept


class CrewAIAgent:
    """Minimal wrapper to register Noema as a CrewAI agent."""

    def __init__(self, loop: ConsciousLoop) -> None:
        self.loop = loop

    def handle_task(self, description: str) -> Dict[str, Any]:
        result = self.loop.run_workflow(Percept(content=description, salience_hint=0.4))
        return {"response": result.action.model_dump(), "tick": self.loop.tick_id}


__all__ = ["CrewAIAgent"]
