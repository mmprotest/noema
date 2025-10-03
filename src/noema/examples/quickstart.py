"""Minimal REPL demonstrating the conscious loop with the dummy backend."""

from __future__ import annotations

import sys

from ..core.backends.dummy import DummyBackend
from ..core.loop import ConsciousLoop
from ..core.types import Percept, RunConfig


def main() -> None:
    config = RunConfig()
    loop = ConsciousLoop(DummyBackend(seed=config.seed), config)
    print("Noema quickstart. Type 'exit' to quit.")
    tick = 0
    while True:
        user = input("You: ")
        if user.strip().lower() in {"exit", "quit"}:
            break
        loop.ingest(Percept(content=user, timestamp=tick, salience_hint=0.4))
        trace = loop.tick()
        action = loop.act()
        print(f"Noema[{trace.tick}]: {action.payload}")
        tick += 1


if __name__ == "__main__":
    main()
