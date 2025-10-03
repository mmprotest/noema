"""FastAPI server exposing loop internals for MCP-compatible tooling."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from ..core.loop import ConsciousLoop


class LoopSnapshot(BaseModel):
    tick: int
    workspace: list[dict]
    last_broadcast: dict | None
    metrics: dict


def create_app(loop: ConsciousLoop) -> FastAPI:
    app = FastAPI(title="Noema MCP Server")

    @app.get("/state", response_model=LoopSnapshot)
    def get_state() -> LoopSnapshot:
        workspace = [c.model_dump() for c in loop.controller.workspace.state()]
        last = loop.last_broadcast.coalition.model_dump() if loop.last_broadcast else None
        metrics = loop.controller.metacog.metrics()
        return LoopSnapshot(
            tick=loop.tick_id,
            workspace=workspace,
            last_broadcast=last,
            metrics=metrics,
        )

    @app.get("/narrative")
    def narrative(last: int = 5) -> list[str]:
        return loop.controller.narrative.last(last)

    return app


__all__ = ["create_app", "LoopSnapshot"]
