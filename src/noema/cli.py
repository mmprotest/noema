"""Command line interface for Noema."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import yaml

from .core.backends.dummy import DummyBackend
from .core.loop import ConsciousLoop
from .core.types import ProcessName, RunConfig
from .reporting.html_report import save_report
from .tasks import microworlds
from .tasks.ablations import apply_ablation
from .tasks.evaluations import aggregate_from_traces

app = typer.Typer(add_completion=False)
eval_app = typer.Typer(help="Evaluation suite")
app.add_typer(eval_app, name="eval")


def _load_config(path: Optional[Path]) -> RunConfig:
    if path is None:
        default = Path(__file__).resolve().parent / "configs" / "defaults.yaml"
        data = yaml.safe_load(default.read_text())
        return RunConfig.model_validate(data)
    data = yaml.safe_load(Path(path).read_text())
    return RunConfig.model_validate(data)


def _backend_from_name(name: str, seed: int):
    name = name.lower()
    if name == "dummy":
        return DummyBackend(seed=seed)
    if name == "openai":
        from .core.backends.openai_backend import OpenAIBackend

        return OpenAIBackend()
    raise typer.BadParameter(f"Unknown model {name}")


def _task_from_name(name: str):
    name = name.lower()
    if name in {"interruption", "interruption_count"}:
        return microworlds.InterruptionCountingTask(length=120, interruption_rate=0.2)
    if name in {"nback", "wm"}:
        return microworlds.NBackTask(n=2, length=60)
    if name in {"change", "change_blindness"}:
        return microworlds.ChangeBlindnessTask(scenes=["Scene A", "Scene B", "Scene A*"])
    raise typer.BadParameter(f"Unknown task {name}")


@app.command()
def run(
    task: str = typer.Option("interruption_count", help="Task to run"),
    model: str = typer.Option("dummy", help="Backend model"),
    ticks: int = typer.Option(50, help="Number of ticks"),
    report: Optional[Path] = typer.Option(None, help="HTML report path"),
    bundle: Optional[Path] = typer.Option(None, help="Bundle output path"),
    config: Optional[Path] = typer.Option(None, help="Config override"),
    disable_reflector: bool = typer.Option(False, help="Disable reflector process"),
) -> None:
    run_config = _load_config(config)
    backend = _backend_from_name(model, run_config.seed)
    loop = ConsciousLoop(backend, run_config)
    env = _task_from_name(task)
    if disable_reflector:
        apply_ablation(loop.controller, [ProcessName.REFLECTOR])
    for _ in range(ticks):
        percept = env.next_percept()
        if percept is None:
            break
        loop.ingest(percept)
        loop.tick()
    report_data = loop.eval()
    if report is not None:
        save_report(loop.traces, report_data, report)
        typer.echo(f"Report written to {report}")
    if bundle is not None:
        path = loop.save_bundle(bundle)
        typer.echo(f"Bundle saved to {path}")
    typer.echo(f"Run metrics: {report_data.metrics}")


@app.command()
def replay(path: Path) -> None:
    from .artifacts.bundles import replay as replay_bundle

    data = replay_bundle(path)
    typer.echo(f"Replayed {data['manifest']['run_id']} with {len(data['traces'])} ticks")


@eval_app.command("battery")
def eval_battery(
    model: str = typer.Option("dummy", help="Backend model to use"),
    ticks: int = typer.Option(100, help="Number of ticks"),
    config: Optional[Path] = typer.Option(None, help="Config override"),
) -> None:
    run_config = _load_config(config)
    backend = _backend_from_name(model, run_config.seed)
    loop = ConsciousLoop(backend, run_config)
    env = microworlds.InterruptionCountingTask(length=ticks, interruption_rate=0.3)
    for _ in range(ticks):
        percept = env.next_percept()
        if percept is None:
            break
        loop.ingest(percept)
        loop.tick()
    report = aggregate_from_traces(loop.traces, backend)
    typer.echo(f"Battery summary: {report.metrics}")


@app.command()
def ui(
    host: str = typer.Option("127.0.0.1", help="Host to bind"),
    port: int = typer.Option(8000, help="Port to bind"),
) -> None:
    from .core.backends.dummy import DummyBackend
    from .core.loop import ConsciousLoop
    from .tasks.microworlds import InterruptionCountingTask
    try:
        from ui.app import build_app
    except ImportError as exc:  # pragma: no cover - optional packaging
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)
    import uvicorn

    config = _load_config(None)
    loop = ConsciousLoop(DummyBackend(seed=config.seed), config)
    env = InterruptionCountingTask(length=30, interruption_rate=0.2)
    percept = env.next_percept()
    if percept:
        loop.ingest(percept)
        loop.tick()
    app_instance = build_app(loop)
    uvicorn.run(app_instance, host=host, port=port)


@app.command()
def ablate(
    disable: Optional[list[str]] = typer.Option(
        None,
        "--disable",
        help="Processes to disable (e.g. reflector, planner)",
    ),
    ticks: int = typer.Option(50, help="Ticks to simulate"),
) -> None:
    run_config = _load_config(None)
    backend = _backend_from_name("dummy", run_config.seed)
    loop = ConsciousLoop(backend, run_config)
    if disable:
        names = [ProcessName(item) for item in disable]
        apply_ablation(loop.controller, names)
    env = microworlds.InterruptionCountingTask(length=ticks, interruption_rate=0.3)
    for _ in range(ticks):
        percept = env.next_percept()
        if percept is None:
            break
        loop.ingest(percept)
        loop.tick()
    report = aggregate_from_traces(loop.traces)
    typer.echo(f"Ablation metrics: {report.metrics}")
