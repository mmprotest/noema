"""Cognitive processes implemented with LLM backends."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..core.backends.base import LLMBackend
from ..instruments.narrative import NarrativeStream
from .memory import WorkingMemory
from .types import Action, Broadcast, Coalition, Percept, ProcessName


def _require_backend(backend: LLMBackend | None) -> LLMBackend:
    if backend is None:
        raise RuntimeError("Backend not configured for this process")
    return backend


def _ensure_structured(resp: Dict[str, Any]) -> tuple[str, float, str]:
    text = str(resp.get("text", "")).strip()
    try:
        conf = float(resp.get("confidence", 0.5))
    except Exception:  # pragma: no cover - defensive
        conf = 0.5
    conf = max(0.0, min(1.0, conf))
    rationale = str(resp.get("rationale_short", "")).strip()[:280]
    return text, conf, rationale


class Process(ABC):
    name: ProcessName

    def __init__(
        self,
        backend: LLMBackend | None,
        temperature: float = 0.0,
        budget: int = 512,
    ) -> None:
        self.backend = backend
        self.temperature = temperature
        self.budget = budget

    @abstractmethod
    def propose(
        self,
        workspace: List[Coalition],
        memory: WorkingMemory,
        last_broadcast: Optional[Broadcast],
    ) -> List[Coalition]:
        raise NotImplementedError

    def after_broadcast(self, broadcast: Broadcast, memory: WorkingMemory) -> None:
        pass

    def act(self, workspace: List[Coalition], memory: WorkingMemory) -> Action:
        return Action()


class Perception(Process):
    name = ProcessName.PERCEPTION

    def __init__(self, backend: LLMBackend, temperature: float = 0.0, budget: int = 512) -> None:
        super().__init__(backend, temperature, budget)
        self._pending: List[Percept] = []

    def ingest(self, percept: Percept) -> None:
        self._pending.append(percept)

    def propose(
        self,
        workspace: List[Coalition],
        memory: WorkingMemory,
        last_broadcast: Optional[Broadcast],
    ) -> List[Coalition]:
        coalitions: List[Coalition] = []
        while self._pending:
            percept = self._pending.pop(0)
            summary = percept.content[:120]
            salience = max(0.1, min(1.2, percept.salience_hint + 0.2))
            coalition = Coalition(
                summary=summary,
                full_text=percept.content,
                salience=salience,
                source="perception",
                confidence=0.8,
            )
            coalitions.append(coalition)
        return coalitions


class Planner(Process):
    name = ProcessName.PLANNER

    def __init__(self, backend: LLMBackend, temperature: float = 0.1, budget: int = 512) -> None:
        super().__init__(backend, temperature, budget)
        self._goal: str = "Maintain coherent dialogue"
        self._last_plan: Optional[str] = None

    def propose(
        self,
        workspace: List[Coalition],
        memory: WorkingMemory,
        last_broadcast: Optional[Broadcast],
    ) -> List[Coalition]:
        prompt = {
            "goal": self._goal,
            "last": last_broadcast.coalition.summary if last_broadcast else None,
            "workspace": [c.summary for c in workspace],
        }
        backend = _require_backend(self.backend)
        resp = backend.generate(
            prompt=json.dumps(prompt),
            system="You plan next steps. Respond JSON with text/confidence/rationale_short.",
            temperature=self.temperature,
            max_tokens=self.budget,
        )
        text, conf, rationale = _ensure_structured(resp)
        coalition = Coalition(
            summary=f"Plan: {text[:80]}",
            full_text=f"Plan step: {text}\nWhy: {rationale}",
            salience=max(0.2, conf + 0.2),
            source="planner",
            confidence=conf,
        )
        self._last_plan = text
        return [coalition]

    def act(self, workspace: List[Coalition], memory: WorkingMemory) -> Action:
        if not self._last_plan:
            return Action(kind="none", payload=None, confidence=0.0)
        return Action(kind="say", payload=self._last_plan, confidence=0.7)


class Reflector(Process):
    name = ProcessName.REFLECTOR

    def propose(
        self,
        workspace: List[Coalition],
        memory: WorkingMemory,
        last_broadcast: Optional[Broadcast],
    ) -> List[Coalition]:
        if not last_broadcast:
            return []
        prompt = {
            "last": last_broadcast.coalition.full_text,
            "confidence": last_broadcast.coalition.confidence,
        }
        backend = _require_backend(self.backend)
        resp = backend.generate(
            prompt=json.dumps(prompt),
            system="You critique plans. Return JSON text/confidence/rationale_short.",
            temperature=self.temperature,
            max_tokens=self.budget,
        )
        text, conf, rationale = _ensure_structured(resp)
        coalition = Coalition(
            summary=f"Reflection: {text[:80]}",
            full_text=f"Reflection: {text}\nKey: {rationale}",
            salience=max(0.1, 0.6 * conf),
            source="reflector",
            confidence=conf,
        )
        return [coalition]


class SelfModel(Process):
    name = ProcessName.SELF_MODEL

    def __init__(self, backend: LLMBackend, temperature: float = 0.05, budget: int = 384) -> None:
        super().__init__(backend, temperature, budget)
        self.identity = "Noema Agent"
        self.constraints = "Functional simulation; not sentient."
        self._narrative = NarrativeStream(redactions=[])

    def propose(
        self,
        workspace: List[Coalition],
        memory: WorkingMemory,
        last_broadcast: Optional[Broadcast],
    ) -> List[Coalition]:
        state = {
            "identity": self.identity,
            "constraints": self.constraints,
            "workspace": [c.summary for c in workspace[-3:]],
        }
        backend = _require_backend(self.backend)
        resp = backend.generate(
            prompt=json.dumps(state),
            system="Maintain identity. Return JSON text/confidence/rationale_short.",
            temperature=self.temperature,
            max_tokens=self.budget,
        )
        text, conf, rationale = _ensure_structured(resp)
        self.identity = self.identity if not text else text
        coalition = Coalition(
            summary=f"Self: {self.identity[:60]}",
            full_text=f"Self description: {self.identity}\nNote: {rationale}",
            salience=0.4 + conf * 0.3,
            source="self_model",
            confidence=conf,
        )
        self._narrative.append(f"Identity reaffirmed: {self.identity}")
        return [coalition]


class Critic(Process):
    name = ProcessName.CRITIC

    def propose(
        self,
        workspace: List[Coalition],
        memory: WorkingMemory,
        last_broadcast: Optional[Broadcast],
    ) -> List[Coalition]:
        risky = []
        for coalition in workspace[-5:]:
            if any(token in coalition.full_text.lower() for token in ("password", "ssn")):
                risky.append(coalition)
        proposals = []
        for coalition in risky:
            text = f"Risk check on: {coalition.summary}"
            proposals.append(
                Coalition(
                    summary=text[:80],
                    full_text=text,
                    salience=max(0.2, coalition.salience * 0.5),
                    source="critic",
                    confidence=0.6,
                )
            )
        return proposals


__all__ = [
    "Process",
    "Perception",
    "Planner",
    "Reflector",
    "SelfModel",
    "Critic",
]
