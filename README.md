# Noema

_Noema_ is a functional simulation of conscious-like control loops for large language models. It delivers a reproducible cognitive workspace with attention, metacognition, and evaluation batteries so you can stress-test robustness—not to claim sentience.

## Features

- Discrete tick-based core loop with processes for perception, planning, reflection, self-modelling, and safety critique.
- Global workspace dynamics with salience-based attention and working + episodic memory stores (in-memory, SQLite, DuckDB).
- Metacognitive telemetry (Brier, ECE, wrong@high-conf) and narrative streams exported as replayable `.noema` bundles.
- Optional OpenTelemetry + structlog instrumentation and a lightweight FastAPI UI for timeline inspection.
- Interop adapters for LangGraph, LlamaIndex, and CrewAI plus an MCP client/server for tool calls and loop introspection.
- Evaluation battery covering interruption recovery, self-reference stability, working-memory span, calibration, and narrative coherence.
- Production scaffolding: Typer CLI, pytest suite, Ruff/Mypy configs, pre-commit, MkDocs docs, GitHub Actions CI.

## Quickstart (60 seconds)

```bash
uv venv && uv pip install -e .[dev,observe,ui]  # or pip install -e .[dev,observe,ui]
noema run --task interruption_count --model dummy --ticks 60 --report report.html --bundle run.noema
noema replay run.noema
python -m noema.examples.quickstart
```

The dummy backend is deterministic and offline friendly. For OpenAI usage install `.[openai]` and set `OPENAI_API_KEY`.

## Architecture

```
Percepts -> Processes -> Attention -> Broadcast -> Memory -> Act
                     |            |            |
                  Metacog      Narrative     Observability
```

The workspace holds salience-weighted coalitions. Attention chooses a winning coalition each tick, broadcasts it, and writes to working memory (with decay) and episodic store. Processes receive broadcasts, update state, and optionally act via actuators.

### Process lineup

| Process     | Role                                       |
|-------------|---------------------------------------------|
| Perception  | Converts stimuli into coalitions            |
| Planner     | Expands goals into actionable steps         |
| Reflector   | Critiques recent broadcasts                 |
| SelfModel   | Maintains identity and constraints          |
| Critic      | Flags unsafe or injected content            |

All language-model calls request structured JSON: `{text, confidence, rationale_short}`.

### Metacognition & Evaluation

Metacognitive metrics (Brier, ECE, Wrong@HighConf) accumulate per tick. Evaluation runners compute:

- Interruption recovery (ticks to resume goal focus)
- Self-reference stability (identity drift)
- Working-memory span (unique plan coverage)
- Calibration (from metacog tracker)
- Narrative coherence (embedding similarity of broadcasts)

Generate reports via `noema run ... --report report.html` or `noema eval`.

### Observability & Bundles

Logging uses `structlog` JSON. Tracing is optional via OpenTelemetry OTLP exporters. Each run can be packaged into a `.noema` bundle containing config, traces, metrics, narrative, and an HTML report.

## UI & MCP

`noema ui` serves a FastAPI app with static TypeScript frontend summarising ticks, workspace contents, and metacognitive trends. The MCP server exposes read-only endpoints (`/state`, `/narrative`) for IDE integration.

## Adapters

- **LangGraph**: wrap the loop as a node, calling `ingress`/`egress`.
- **LlamaIndex**: bridge retrieval memory using loop working memory.
- **CrewAI**: delegate tasks via `CrewAIAgent.handle_task`.

Each adapter has a runnable example under `src/noema/examples/`.

## Security & Ethics

- Functional simulation only—Noema makes **no claims of sentience**.
- Anthropomorphism toggles ensure outputs emphasise simulation.
- Basic PII redaction via configurable rules (`defaults.yaml`).
- MCP client restricts filesystem access to the workspace and disables HTTP by default.

## Sharing Results

`noema run ... --bundle out.noema` stores a replayable artifact. Share the bundle to reproduce metrics and narratives.

## Development

```bash
uv venv && uv pip install -e .[dev,observe,ui]
pre-commit install
pytest -q
mkdocs serve
```

CI (GitHub Actions) runs linting (Ruff), typing (Mypy), tests, docs build, and uploads a sample HTML report artifact from a dummy run.

## Documentation

Docs are powered by MkDocs Material. Key pages: overview, API reference, adapters, evaluations. ASCII diagrams illustrate the control loop and memory flows.
