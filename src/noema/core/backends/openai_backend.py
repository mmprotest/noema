"""OpenAI backend implementation."""

from __future__ import annotations

import os
from typing import List

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover - optional dependency
    raise ImportError("openai extra required: pip install noema[openai]") from exc

from .base import LLMBackend


class OpenAIBackend:
    name = "openai"

    def __init__(self, model: str = "gpt-3.5-turbo", temperature: float = 0.2) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.default_temperature = temperature

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 512,
    ) -> dict:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                temperature=temperature if temperature is not None else self.default_temperature,
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
                messages=messages,
            )
        except Exception as exc:  # pragma: no cover - network
            raise RuntimeError(f"OpenAI error: {exc}")
        content = completion.choices[0].message.content or "{}"
        return self._ensure_json(content)

    def _ensure_json(self, payload: str) -> dict:
        import json

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = {"text": payload, "confidence": 0.5, "rationale_short": "unstructured"}
        return data

    def embed(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embeddings.create(model="text-embedding-3-small", input=texts)
        except Exception as exc:  # pragma: no cover - network
            raise RuntimeError(f"OpenAI embed error: {exc}")
        return [list(item.embedding) for item in response.data]

    def cost_estimator(self, tokens_in: int, tokens_out: int) -> float:
        return 0.000001 * (tokens_in + tokens_out)


__all__ = ["OpenAIBackend"]
