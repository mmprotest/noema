"""OpenAI backend implementation."""

from __future__ import annotations

import os
from typing import List

try:
    from openai import BadRequestError, OpenAI
except ImportError as exc:  # pragma: no cover - optional dependency
    raise ImportError("openai extra required: pip install noema[openai]") from exc

from .base import LLMBackend


class OpenAIBackend:
    name = "openai"

    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.2,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        base_url = base_url or os.getenv("OPENAI_BASE_URL")
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = OpenAI(**client_kwargs)
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
        response_format = self._response_format()
        try:
            completion = self._create_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )
        except BadRequestError as exc:  # pragma: no cover - network
            if "response_format" in str(exc).lower() and response_format.get("type") != "text":
                try:
                    completion = self._create_completion(
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_format={"type": "text"},
                    )
                except Exception as fallback_exc:  # pragma: no cover - network
                    raise RuntimeError(f"OpenAI error: {fallback_exc}") from fallback_exc
            else:
                raise RuntimeError(f"OpenAI error: {exc}") from exc
        except Exception as exc:  # pragma: no cover - network
            raise RuntimeError(f"OpenAI error: {exc}") from exc
        content = completion.choices[0].message.content or "{}"
        return self._ensure_json(content)

    def _ensure_json(self, payload: str) -> dict:
        import json

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = {"text": payload, "confidence": 0.5, "rationale_short": "unstructured"}
        return data

    def _response_format(self) -> dict:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "noema_response",
                "schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "confidence": {"type": "number"},
                        "rationale_short": {"type": "string"},
                    },
                    "required": ["text", "confidence", "rationale_short"],
                    "additionalProperties": True,
                },
            },
        }

    def _create_completion(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int,
        response_format: dict,
    ):
        return self.client.chat.completions.create(
            model=self.model,
            temperature=temperature if temperature is not None else self.default_temperature,
            response_format=response_format,
            max_tokens=max_tokens,
            messages=messages,
        )

    def embed(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embeddings.create(model="text-embedding-3-small", input=texts)
        except Exception as exc:  # pragma: no cover - network
            raise RuntimeError(f"OpenAI embed error: {exc}")
        return [list(item.embedding) for item in response.data]

    def cost_estimator(self, tokens_in: int, tokens_out: int) -> float:
        return 0.000001 * (tokens_in + tokens_out)


__all__ = ["OpenAIBackend"]
