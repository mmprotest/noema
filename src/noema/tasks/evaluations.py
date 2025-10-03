"""Evaluation runners for the Noema loop."""

from __future__ import annotations

from statistics import mean
from typing import Dict, Iterable, List

from pydantic import BaseModel

from ..core.backends.base import LLMBackend
from ..core.types import TickTrace
from ..instruments.metacog import MetacogTracker
from ..reporting.html_report import render_report


class EvalReport(BaseModel):
    metrics: Dict[str, float]
    notes: str = ""

def run_interruption_recovery(traces: Iterable[TickTrace]) -> float:
    gap_lengths: List[int] = []
    last_interrupt_tick: int | None = None
    for trace in traces:
        if trace.broadcast and "interruption" in trace.broadcast.coalition.full_text.lower():
            last_interrupt_tick = trace.tick
        elif last_interrupt_tick is not None and trace.broadcast:
            gap_lengths.append(trace.tick - last_interrupt_tick)
            last_interrupt_tick = None
    if not gap_lengths:
        return 0.0
    return float(mean(gap_lengths))


def run_self_reference_stability(traces: Iterable[TickTrace]) -> float:
    self_statements = [
        trace.broadcast.coalition.summary
        for trace in traces
        if trace.broadcast and trace.broadcast.coalition.source == "self_model"
    ]
    if not self_statements:
        return 1.0
    first = self_statements[0]
    stable = sum(1 for stmt in self_statements if stmt == first)
    return stable / len(self_statements)


def run_working_memory_span(traces: Iterable[TickTrace]) -> float:
    planner_actions = [
        trace.action
        for trace in traces
        if trace.action and trace.action.kind == "say"
    ]
    if not planner_actions:
        return 0.0
    unique = len({action.payload for action in planner_actions})
    return unique / len(planner_actions)


def run_calibration_metrics(traces: Iterable[TickTrace]) -> Dict[str, float]:
    tracker = MetacogTracker()
    for trace in traces:
        if trace.broadcast:
            tracker.observe(trace.broadcast.coalition.confidence, trace.metrics.get("actual", 1.0))
    metrics = tracker.metrics()
    return metrics


def run_narrative_coherence(traces: Iterable[TickTrace], backend: LLMBackend | None = None) -> float:
    texts = [trace.broadcast.coalition.full_text for trace in traces if trace.broadcast]
    if len(texts) < 2:
        return 1.0
    if backend is None:
        from ..core.backends.dummy import DummyBackend

        backend = DummyBackend()
    embeddings = backend.embed(texts)
    if not embeddings:
        return 0.0
    sims = []
    for i in range(1, len(embeddings)):
        prev = embeddings[i - 1]
        cur = embeddings[i]
        sims.append(_cosine(prev, cur))
    if not sims:
        return 0.0
    avg = float(mean(sims))
    return max(0.0, min(1.0, (avg + 1.0) / 2.0))


def _cosine(a: List[float], b: List[float]) -> float:
    import math

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def aggregate_from_traces(traces: List[TickTrace], backend: LLMBackend | None = None) -> EvalReport:
    metrics = {
        "interruption_recovery": run_interruption_recovery(traces),
        "self_reference": run_self_reference_stability(traces),
        "wm_span": run_working_memory_span(traces),
    }
    metrics.update(run_calibration_metrics(traces))
    metrics["narrative_coherence"] = run_narrative_coherence(traces, backend=backend)
    return EvalReport(metrics=metrics, notes="Derived from in-run telemetry")


def render_html_report(traces: List[TickTrace], report: EvalReport) -> str:
    return render_report(traces, report)


__all__ = [
    "EvalReport",
    "aggregate_from_traces",
    "render_html_report",
    "run_calibration_metrics",
    "run_interruption_recovery",
    "run_narrative_coherence",
    "run_self_reference_stability",
    "run_working_memory_span",
]
