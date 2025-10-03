"""Illustrates CrewAI adapter usage."""

from __future__ import annotations

from ..core.backends.dummy import DummyBackend
from ..core.loop import ConsciousLoop
from ..core.types import RunConfig


def main() -> None:
    try:
        from ..interop.crewai_adapter import CrewAIAgent
    except ImportError as exc:  # pragma: no cover
        print(exc)
        return

    loop = ConsciousLoop(DummyBackend(seed=7), RunConfig())
    agent = CrewAIAgent(loop)
    print(agent.handle_task("Summarise daily status"))


if __name__ == "__main__":
    main()
