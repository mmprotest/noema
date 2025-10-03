"""Backend interfaces for language models."""

from __future__ import annotations

from typing import Protocol


class LLMBackend(Protocol):
    """Minimal interface implemented by backends."""

    name: str

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> dict:
        """Return a structured response."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return deterministic embeddings for the provided texts."""

    def cost_estimator(self, tokens_in: int, tokens_out: int) -> float:
        """Estimate cost of a call (USD)."""


__all__ = ["LLMBackend"]
