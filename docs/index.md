# Noema Documentation

## Overview

Noema orchestrates a conscious-like control loop for LLM agents. It is a **functional simulation** intended for evaluation and research—not a claim of sentience.

```
+-----------+     +-----------+     +------------+
| Percepts  | --> | Processes | --> | Attention  |
+-----------+     +-----------+     +------------+
                                         |
                                         v
                                  +-------------+
                                  | Workspace   |
                                  +-------------+
                                         |
                                         v
                                +------------------+
                                | Memory & Actions |
                                +------------------+
```

## Core Concepts

### Processes

- **Perception** ingests stimuli.
- **Planner** advances goals.
- **Reflector** critiques outputs.
- **SelfModel** maintains identity and constraints.
- **Critic** evaluates safety and PII.

All processes emit salience-weighted coalitions competing for broadcast.

### Consciousness Workflow

The public API exposes :class:`~noema.core.loop.ConsciousLoop.run_workflow`, which
executes a complete perceive → deliberate → act cycle. Each workflow:

- Consumes any pending :class:`~noema.core.types.Percept` objects,
- Advances the controller for ``RunConfig.workflow_ticks`` ticks (or more if
  multiple percepts are queued),
- Aggregates the highest-confidence :class:`~noema.core.types.Action`, and
- Returns recent narrative events for UI display.

Interactive clients such as the CLI and adapters now call ``run_workflow`` to
ensure multi-step deliberation before responding, leading to more coherent
utterances compared to single-tick interactions.

### Memory

Working memory decays exponentially, while episodic memory persists via in-memory, SQLite, or DuckDB backends.

```
WM entries --decay--> lower salience
        \
         \--> Episodic store (searchable)
```

### Metacognition

Each broadcast yields confidence metrics. We compute Brier score, expected calibration error, and Wrong@HighConf. Results power the evaluation battery and UI charts.

## CLI

- `noema run` executes a task and optionally emits HTML reports or `.noema` bundles.
- `noema eval` runs the evaluation battery on the dummy backend.
- `noema ui` launches the FastAPI timeline viewer.
- `noema replay` reads bundles without network access.

## Adapters

Use the adapters in `src/noema/interop/` to link Noema with LangGraph, LlamaIndex, or CrewAI. Each has a runnable example script.

## MCP & Observability

The MCP client/server provide limited filesystem and narrative introspection. Logging uses `structlog` JSON. Tracing can be enabled via `noema.observe.otel.configure_otel()`.

## Tests

Run `pytest` to execute loop, metacognition, evaluation, and adapter smoke tests. CI ensures determinism and documentation builds.
