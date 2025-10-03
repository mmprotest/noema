from __future__ import annotations

import pytest

from noema.core.backends.dummy import DummyBackend
from noema.core.loop import ConsciousLoop
from noema.core.types import Percept, RunConfig


def _loop() -> ConsciousLoop:
    config = RunConfig()
    return ConsciousLoop(DummyBackend(seed=config.seed), config)


def test_langgraph_adapter_round_trip() -> None:
    try:
        from noema.interop.langgraph_adapter import LangGraphAdapter
    except ImportError:
        pytest.skip("langgraph not installed")
    loop = _loop()
    adapter = LangGraphAdapter(loop)
    adapter.ingress("hello", tick=0)
    assert adapter.egress()["tick"] == loop.tick_id


def test_llamaindex_adapter_round_trip() -> None:
    try:
        from noema.interop.llamaindex_adapter import LlamaIndexMemory
    except ImportError:
        pytest.skip("llama-index not installed")
    loop = _loop()
    memory = LlamaIndexMemory(loop)
    memory.add("doc")
    assert "action" in memory.query("doc")


def test_crewai_adapter_round_trip() -> None:
    try:
        from noema.interop.crewai_adapter import CrewAIAgent
    except ImportError:
        pytest.skip("crewai not installed")
    loop = _loop()
    agent = CrewAIAgent(loop)
    result = agent.handle_task("status")
    assert result["tick"] == loop.tick_id
