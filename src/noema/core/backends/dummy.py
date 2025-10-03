"""Deterministic backend used for tests and offline work."""

from __future__ import annotations

import hashlib
import json
import random
from typing import List

from .base import LLMBackend


class DummyBackend:
    """Rule-based backend returning predictable structured outputs."""

    name = "dummy"

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 256,
    ) -> dict:
        digest = hashlib.sha256((prompt + (system or "") + str(self.seed)).encode()).hexdigest()
        conf = (int(digest[:4], 16) % 100) / 100
        rationale = f"deterministic rationale {digest[4:20]}"
        text = self._summarise(prompt)
        return {"text": text, "confidence": conf / 100 + 0.5, "rationale_short": rationale[:120]}

    def _summarise(self, prompt: str) -> str:
        try:
            data = json.loads(prompt)
            if isinstance(data, dict):
                if "goal" in data and "workspace" in data:
                    workspace = ", ".join(data.get("workspace", [])[-2:])
                    return f"Next step towards {data['goal']} via {workspace or 'initial step'}"
                if "identity" in data:
                    return data.get("identity", "Noema Agent")
                if "last" in data:
                    return f"Review: {str(data['last'])[:40]}"
        except json.JSONDecodeError:
            pass
        return prompt[:80]

    def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            seed = int.from_bytes(hashlib.md5(text.encode()).digest()[:8], "big")
            rng = random.Random(seed)
            embeddings.append([rng.uniform(-1.0, 1.0) for _ in range(32)])
        return embeddings

    def cost_estimator(self, tokens_in: int, tokens_out: int) -> float:
        return 0.0


__all__ = ["DummyBackend"]
