"""LlamaIndex adapter stub."""

from __future__ import annotations

from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    import llama_index
except ImportError:  # pragma: no cover
    llama_index = None

from ..core.loop import ConsciousLoop
from ..core.types import Percept


class LlamaIndexMemory:
    def __init__(self, loop: ConsciousLoop) -> None:
        self.loop = loop

    def add(self, text: str) -> None:
        self.loop.run_workflow(Percept(content=text))

    def query(self, text: str) -> Dict[str, Any]:
        result = self.loop.run_workflow(Percept(content=text, salience_hint=0.5))
        return {"action": result.action.model_dump()}


__all__ = ["LlamaIndexMemory"]
