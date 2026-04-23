"""Standalone HTML trace viewer.

Reads every JSONL file under traces/ and produces a single results/trace_viewer.html
with collapsible cells per (harness, task, run). Zero external JS — inline only.
"""
from __future__ import annotations

import html
import json
from dataclasses import dataclass, field
from pathlib import Path

from .config import RESULTS_DIR, TRACES_DIR


@dataclass
class _Run:
    harness: str
    task_id: str
    run_id: str
    path: Path
    events: list[dict] = field(default_factory=list)


def _load_runs(traces_dir: Path) -> list[_Run]:
    runs: list[_Run] = []
    if not traces_dir.exists():
        return runs
    for harness_dir in sorted(p for p in traces_dir.iterdir() if p.is_dir()):
        for task_dir in sorted(p for p in harness_dir.iterdir() if p.is_dir()):
            for trace_file in sorted(task_dir.glob("*.jsonl")):
                events = []
                for line in trace_file.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        try:
                            events.append(json.loads(line))
                        except Exception:
                            pass
                runs.append(_Run(
                    harness=harness_dir.name,
                    task_id=task_dir.name,
                    run_id=trace_file.stem,
                    path=trace_file,
                    events=events,
                ))
    return runs


_CSS = """
body { font-family: -apple-system, system-ui, monospace; margin: 0; padding: 1.5em; background: #fafaf7; color: #222; }
h1 { margin: 0 0 0.4em; font-size: 1.5em; }
.meta { color: #666; margin-bottom: 1.5em; font-size: 0.9em; }
details.run { background: #fff; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 0.5em; padding: 0.5em 0.8em; }
details.run > summary { cursor: pointer; font-weight: 600; list-style: none; }
details.run > summary::-webkit-details-marker { display: none; }
details.run > summary::before { content: "▸ "; }
details.run[open] > summary::before { content: "▾ "; }
.badge { display: inline-block; padding: 1px 6px; margin-left: 0.5em; border-radius: 3px; font-size: 0.75em; font-weight: 500; }
.badge.success { background: #d1fae5; color: #065f46; }
.badge.fail { background: #fee2e2; color: #991b1b; }
.badge.harness { background: #e0e7ff; color: #3730a3; }
.badge.task { background: #fef3c7; color: #78350f; }
.event { margin: 0.3em 0 0.3em 1em; padding: 0.3em 0.5em; border-left: 2px solid #ccc; font-size: 0.85em; }
.event.model_call { border-left-color: #6366f1; }
.event.model_response { border-left-color: #8b5cf6; }
.event.tool_call { border-left-color: #ea580c; }
.event.tool_result { border-left-color: #0891b2; }
.event.run_end { border-left-color: #059669; font-weight: 500; }
.event.run_error { border-left-color: #dc2626; color: #991b1b; }
.event .type { font-weight: 600; color: #444; }
.event pre { margin: 0.2em 0 0; white-space: pre-wrap; word-break: break-word; color: #444; font-size: 0.82em; max-height: 200px; overflow: auto; background: #f4f4f0; padding: 0.3em 0.5em; border-radius: 3px; }
.filter { margin-bottom: 1em; font-size: 0.9em; }
.filter select { padding: 0.3em; margin-right: 0.5em; }
"""


def _event_html(ev: dict) -> str:
    ev_type = ev.get("type", "")
    payload = {k: v for k, v in ev.items() if k not in ("type", "ts")}
    summary_bits = [f'<span class="type">{html.escape(ev_type)}</span>']
    if ev_type == "tool_call":
        summary_bits.append(html.escape(f" {ev.get('name', '')}({ev.get('args', {})})"))
    elif ev_type == "tool_result":
        summary_bits.append(html.escape(f" {ev.get('name', '')} ({ev.get('output_len', 0)} chars)"))
    elif ev_type == "model_response":
        summary_bits.append(html.escape(
            f" in={ev.get('input_tokens', 0)} out={ev.get('output_tokens', 0)} "
            f"lat={ev.get('latency_s', 0):.1f}s stop={ev.get('stop_reason', '')}"
        ))
    elif ev_type == "run_end":
        summary_bits.append(html.escape(
            f" {ev.get('stop_reason', '')} tokens={ev.get('input_tokens', 0)}+{ev.get('output_tokens', 0)}"
        ))
    summary = "".join(summary_bits)
    body = html.escape(json.dumps(payload, indent=2, default=str))
    return (
        f'<div class="event {html.escape(ev_type)}">{summary}'
        f'<pre>{body}</pre></div>'
    )


def _run_html(run: _Run) -> str:
    end = next((e for e in reversed(run.events) if e.get("type") == "run_end"), {})
    stop = end.get("stop_reason", "")
    success = stop == "submitted"
    badge = '<span class="badge success">submitted</span>' if success else f'<span class="badge fail">{html.escape(stop or "incomplete")}</span>'
    header = (
        f'<span class="badge harness">{html.escape(run.harness)}</span>'
        f'<span class="badge task">{html.escape(run.task_id)}</span>'
        f' run <code>{html.escape(run.run_id)}</code> {badge}'
    )
    events_html = "\n".join(_event_html(e) for e in run.events)
    return (
        f'<details class="run" data-harness="{html.escape(run.harness)}" data-task="{html.escape(run.task_id)}">'
        f'<summary>{header}</summary>{events_html}</details>'
    )


def _filter_script(harnesses: list[str], tasks: list[str]) -> str:
    # Pure inline JS, no external deps.
    return (
        "<script>\n"
        "function applyFilters(){\n"
        "  const h = document.getElementById('fh').value;\n"
        "  const t = document.getElementById('ft').value;\n"
        "  document.querySelectorAll('details.run').forEach(el => {\n"
        "    const mh = (h === '' || el.dataset.harness === h);\n"
        "    const mt = (t === '' || el.dataset.task === t);\n"
        "    el.style.display = (mh && mt) ? '' : 'none';\n"
        "  });\n"
        "}\n"
        "</script>"
    )


def build_viewer(traces_dir: Path | None = None, out: Path | None = None) -> Path:
    traces_dir = traces_dir or TRACES_DIR
    out = out or RESULTS_DIR / "trace_viewer.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    runs = _load_runs(traces_dir)
    harnesses = sorted({r.harness for r in runs})
    tasks = sorted({r.task_id for r in runs})
    options_h = "".join(f'<option value="{html.escape(h)}">{html.escape(h)}</option>' for h in harnesses)
    options_t = "".join(f'<option value="{html.escape(t)}">{html.escape(t)}</option>' for t in tasks)
    body = "\n".join(_run_html(r) for r in runs)
    page = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>harness_eng trace viewer</title>
<style>{_CSS}</style></head><body>
<h1>harness_eng trace viewer</h1>
<div class="meta">{len(runs)} runs across {len(harnesses)} harnesses and {len(tasks)} tasks.</div>
<div class="filter">
  Harness:
  <select id="fh" onchange="applyFilters()"><option value="">(all)</option>{options_h}</select>
  Task:
  <select id="ft" onchange="applyFilters()"><option value="">(all)</option>{options_t}</select>
</div>
{body}
{_filter_script(harnesses, tasks)}
</body></html>
"""
    out.write_text(page, encoding="utf-8")
    return out
