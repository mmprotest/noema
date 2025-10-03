"""Very small YAML parser for the project configuration."""

from __future__ import annotations

import json
from typing import Any, Dict


def safe_load(text: str) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(0, root)]
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.lstrip()
        while indent < stack[-1][0]:
            stack.pop()
        container = stack[-1][1]
        if stripped.startswith("- "):
            value = _coerce(stripped[2:].strip())
            if isinstance(container, dict):
                if len(stack) < 2:
                    raise ValueError("Invalid YAML structure")
                parent_indent, parent_container = stack[-2]
                key = None
                for k, v in parent_container.items():
                    if v is container:
                        key = k
                        break
                new_list: list[Any] = []
                parent_container[key] = new_list  # type: ignore[index]
                stack[-1] = (stack[-1][0], new_list)
                container = new_list
            if not isinstance(container, list):
                raise ValueError("List item without list container")
            container.append(value)
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            new_container: Dict[str, Any] = {}
            if isinstance(container, dict):
                container[key] = new_container
            else:
                raise ValueError("Cannot assign mapping to list")
            stack.append((indent + 2, new_container))
        else:
            if isinstance(container, dict):
                container[key] = _coerce(value)
            else:
                raise ValueError("Cannot assign value to list container")
    return root


def _coerce(value: str) -> Any:
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


__all__ = ["safe_load"]
