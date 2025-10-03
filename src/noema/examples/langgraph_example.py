"""Illustrates using the LangGraph adapter."""

from __future__ import annotations

from ..core.backends.dummy import DummyBackend
from ..core.loop import ConsciousLoop
from ..core.types import Percept, RunConfig


def main() -> None:
    try:
        from ..interop.langgraph_adapter import LangGraphAdapter
    except ImportError as exc:  # pragma: no cover - optional
        print(exc)
        return

    config = RunConfig()
    loop = ConsciousLoop(DummyBackend(seed=config.seed), config)
    adapter = LangGraphAdapter(loop)
    adapter.ingress("Hello graph", tick=0)
    print(adapter.egress())


if __name__ == "__main__":
    main()
