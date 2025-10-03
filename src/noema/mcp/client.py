"""Minimal MCP client for sandboxed tool calls."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import requests


@dataclass
class MCPClient:
    """Client providing a limited set of MCP-compatible operations."""

    root: Path
    allow_http: bool = False

    def __post_init__(self) -> None:
        self.root = self.root.resolve()

    def read_file(self, relative_path: str) -> str:
        path = (self.root / relative_path).resolve()
        if not path.is_file() or self.root not in path.parents and path != self.root:
            raise PermissionError("Path outside workspace")
        return path.read_text(encoding="utf-8")

    def list_dir(self, relative_path: str = ".") -> List[str]:
        path = (self.root / relative_path).resolve()
        if self.root not in path.parents and path != self.root:
            raise PermissionError("Path outside workspace")
        return sorted(p.name for p in path.iterdir())

    def http_get(self, url: str) -> str:
        if not self.allow_http:
            raise PermissionError("HTTP access disabled")
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.text


__all__ = ["MCPClient"]
