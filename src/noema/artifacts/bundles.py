"""Utilities for persisting and replaying Noema runs."""

from __future__ import annotations

import json
import uuid
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from ..reporting.html_report import render_report
from ..tasks.evaluations import aggregate_from_traces


def _serialise_coalition(coalition) -> Dict[str, Any]:
    return coalition.model_dump() if coalition else None


def _serialise_action(action) -> Dict[str, Any] | None:
    if action is None:
        return None
    return action.model_dump()


def create_bundle(path: str | Path, loop) -> str:
    from ..core.types import TickTrace

    traces = getattr(loop, "traces", [])
    config = loop.config.model_dump()
    report = aggregate_from_traces(traces)
    html = render_report(traces, report)
    run_id = str(uuid.uuid4())
    manifest = {
        "run_id": run_id,
        "model": getattr(loop.backend, "name", "unknown"),
        "seed": loop.config.seed,
    }
    tmp_path = Path(path)
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(tmp_path, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        archive.writestr("config.json", json.dumps(config, indent=2))
        archive.writestr("report.html", html)
        serialised_traces = []
        for trace in traces:
            serialised_traces.append(
                {
                    "tick": trace.tick,
                    "broadcast": _serialise_coalition(trace.broadcast.coalition)
                    if trace.broadcast
                    else None,
                    "workspace_state": [c.model_dump() for c in trace.workspace_state],
                    "processes": {k.value: [c.model_dump() for c in v] for k, v in trace.processes_considered.items()},
                    "action": _serialise_action(trace.action),
                    "metrics": trace.metrics,
                }
            )
        archive.writestr("traces.json", json.dumps(serialised_traces, indent=2))
    return str(tmp_path)


def replay(path: str | Path) -> Dict[str, Any]:
    with zipfile.ZipFile(Path(path), "r") as archive:
        manifest = json.loads(archive.read("manifest.json"))
        traces = json.loads(archive.read("traces.json"))
        config = json.loads(archive.read("config.json"))
    return {"manifest": manifest, "traces": traces, "config": config}


__all__ = ["create_bundle", "replay"]
