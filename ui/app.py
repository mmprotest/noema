"""FastAPI application serving the Noema UI."""

from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from noema.core.loop import ConsciousLoop


BASE = Path(__file__).parent
STATIC = BASE / "static"


def build_app(loop: ConsciousLoop) -> FastAPI:
    app = FastAPI(title="Noema UI")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return (STATIC / "index.html").read_text(encoding="utf-8")

    @app.get("/api/run/state")
    async def state() -> dict:
        return {
            "tick": loop.tick_id,
            "workspace": [c.model_dump() for c in loop.controller.workspace.state()],
            "metrics": loop.controller.metacog.metrics(),
        }

    @app.get("/api/run/narrative")
    async def narrative(limit: int = 10) -> List[str]:
        return loop.controller.narrative.last(limit)

    @app.get("/api/run/traces")
    async def traces() -> list[dict]:
        payload = []
        for trace in loop.traces:
            payload.append(
                {
                    "tick": trace.tick,
                    "broadcast": trace.broadcast.coalition.model_dump() if trace.broadcast else None,
                    "metrics": trace.metrics,
                }
            )
        return payload

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app


__all__ = ["build_app"]
