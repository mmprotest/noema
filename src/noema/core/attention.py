"""Attention selection for the global workspace."""

from __future__ import annotations

import hashlib
import math
import random
from typing import Iterable, List

from .types import Coalition


def _embedding(text: str) -> List[float]:
    seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")
    rng = random.Random(seed)
    return [rng.uniform(-1.0, 1.0) for _ in range(32)]


def _novelty(candidate: Coalition, ws_state: Iterable[Coalition]) -> float:
    if not ws_state:
        return 1.0
    cand_vec = _embedding(candidate.summary)
    sims = []
    for coalition in ws_state:
        vec = _embedding(coalition.summary)
        sims.append(_cosine(cand_vec, vec))
    if not sims:
        return 1.0
    avg_sim = sum(sims) / len(sims)
    return max(0.1, 1.0 - avg_sim)


def _tie_break(value: float, text: str, seed: int = 0) -> float:
    digest = hashlib.md5((text + str(seed)).encode("utf-8")).digest()
    jitter = int.from_bytes(digest[:4], "big") / 2**32
    return value + jitter * 1e-3


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class Attention:
    """Implements salience competition with novelty and tie-breaking."""

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed

    def select(self, candidates: List[Coalition], ws_state: List[Coalition]) -> Coalition:
        if not candidates:
            raise ValueError("No candidates to select from")
        scored = []
        for coalition in candidates:
            novelty = _novelty(coalition, ws_state)
            score = coalition.bounded_salience * novelty
            scored.append((score, coalition))
        scored.sort(key=lambda item: _tie_break(item[0], item[1].summary, self.seed), reverse=True)
        return scored[0][1]


__all__ = ["Attention"]
