"""Actuator implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..core.types import Action


@dataclass
class TextActuator:
    """Collects agent speech for later inspection."""

    history: List[str]

    def perform(self, action: Action) -> None:
        if action.kind == "say" and isinstance(action.payload, str):
            self.history.append(action.payload)


__all__ = ["TextActuator"]
