"""Illustrates LlamaIndex adapter usage."""

from __future__ import annotations

from ..core.backends.dummy import DummyBackend
from ..core.loop import ConsciousLoop
from ..core.types import RunConfig


def main() -> None:
    try:
        from ..interop.llamaindex_adapter import LlamaIndexMemory
    except ImportError as exc:  # pragma: no cover
        print(exc)
        return

    loop = ConsciousLoop(DummyBackend(seed=7), RunConfig())
    memory = LlamaIndexMemory(loop)
    memory.add("Document: The sky is blue")
    print(memory.query("What colour is the sky?"))


if __name__ == "__main__":
    main()
