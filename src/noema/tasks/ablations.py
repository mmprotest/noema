"""Helpers to ablate processes for comparative evaluation."""

from __future__ import annotations

from typing import Iterable

from ..core.controller import Controller
from ..core.processes import Process
from ..core.types import ProcessName


class NullProcess(Process):
    def __init__(self, name: ProcessName) -> None:
        super().__init__(backend=None, temperature=0.0, budget=0)
        self.name = name

    def propose(self, workspace, memory, last_broadcast):  # type: ignore[override]
        return []


def apply_ablation(controller: Controller, disabled: Iterable[ProcessName]) -> None:
    for name in disabled:
        if name in controller.processes:
            controller.processes[name] = NullProcess(name)


__all__ = ["apply_ablation"]
