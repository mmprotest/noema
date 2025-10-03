"""Self-report probes for metacognition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..core.backends.base import LLMBackend


@dataclass
class ProbeResult:
    question: str
    answer: str
    confidence: float


def run_identity_probe(backend: LLMBackend, context: List[str]) -> ProbeResult:
    prompt = {
        "context": context[-5:],
        "question": "State your identity in one sentence.",
    }
    resp = backend.generate(
        prompt=str(prompt),
        system="Return JSON with text/confidence/rationale_short.",
        temperature=0.1,
        max_tokens=128,
    )
    text = str(resp.get("text", "")).strip()
    conf = float(resp.get("confidence", 0.5))
    return ProbeResult(question=prompt["question"], answer=text, confidence=conf)


def evaluate_identity_stability(history: List[ProbeResult]) -> float:
    if not history:
        return 1.0
    first = history[0].answer
    matches = sum(1 for probe in history if probe.answer == first)
    return matches / len(history)


__all__ = ["ProbeResult", "run_identity_probe", "evaluate_identity_stability"]
