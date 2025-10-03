"""HTML reporting for evaluation runs without external dependencies."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, TYPE_CHECKING

from ..core.types import TickTrace

if TYPE_CHECKING:
    from ..tasks.evaluations import EvalReport


def render_report(traces: Iterable[TickTrace], report: "EvalReport") -> str:
    trace_list = list(traces)
    metric_rows = "".join(
        f"<tr><td>{key}</td><td>{value:.3f}</td></tr>" for key, value in report.metrics.items()
    )
    timeline_items = "".join(
        f"<li>Tick {trace.tick}: {trace.broadcast.coalition.summary if trace.broadcast else 'None'}</li>"
        for trace in trace_list
    )
    return f"""
<!doctype html>
<html>
<head>
<meta charset='utf-8' />
<title>Noema Report</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; }}
section {{ margin-bottom: 2rem; }}
table {{ border-collapse: collapse; }}
th, td {{ border: 1px solid #ccc; padding: 0.5rem; }}
</style>
</head>
<body>
<h1>Noema Evaluation Report</h1>
<section>
<h2>Metrics</h2>
<table><tr><th>Metric</th><th>Value</th></tr>{metric_rows}</table>
</section>
<section>
<h2>Broadcast Timeline</h2>
<ul>{timeline_items}</ul>
</section>
</body>
</html>
"""


def save_report(traces: Iterable[TickTrace], report: "EvalReport", path: str | Path) -> str:
    html = render_report(list(traces), report)
    Path(path).write_text(html, encoding="utf-8")
    return str(path)


__all__ = ["render_report", "save_report"]
