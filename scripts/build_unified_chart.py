"""
Build a unified chart showing all eight benchmarked harnesses across both task
types in one image.

Why: the per-task-type charts in writeup/ each show 5 harnesses (correct for
their data) but a reader scanning images can come away thinking the experiment
benchmarked 5 harnesses, not 8. This script produces a single combined view
that puts all eight unique harnesses in one frame with a clear legend showing
which task type each row applies to.

Output: writeup/unified-success-glm-20260423.png

Usage:
    python scripts/build_unified_chart.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RUN_FILES = [
    ROOT / "results" / "runs" / "20260423_211551_final.jsonl",
    ROOT / "results" / "runs" / "20260423_220318_html.jsonl",
]
OUT = ROOT / "writeup" / "unified-success-glm-20260423.png"

ORDER = [
    "single_shot",
    "react",
    "plan_execute",
    "reflexion",
    "minimal",
    "chain_of_thought",
    "test_driven",
    "retry_on_fail",
]

GREEN = "#3a7d44"
BLUE = "#3a5c7d"
GREY = "#cccccc"


def load_aggregates() -> dict[str, dict[str, dict]]:
    by_harness_task: dict[tuple[str, str], list] = defaultdict(list)
    for path in RUN_FILES:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            by_harness_task[(d["harness"], d.get("task_type", ""))].append(d)

    agg: dict[str, dict[str, dict]] = {}
    for (harness, task_type), rows in by_harness_task.items():
        succ = sum(1 for r in rows if r.get("success"))
        n = len(rows)
        wall = sum(r.get("wall_clock_s", 0) for r in rows)
        tok_in = sum(r.get("input_tokens", 0) for r in rows)
        agg.setdefault(harness, {})[task_type] = {
            "successes": succ,
            "trials": n,
            "rate": succ / n if n else 0.0,
            "wall_total_s": wall,
            "input_tokens_total": tok_in,
        }
    return agg


def main() -> None:
    agg = load_aggregates()
    n_harnesses = len(ORDER)

    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(11, 8.5), gridspec_kw={"height_ratios": [3, 2]})

    y_pos = np.arange(n_harnesses)
    bar_h = 0.35

    html_rates = []
    code_rates = []
    html_wall = []
    code_wall = []
    for h in ORDER:
        h_html = agg.get(h, {}).get("html_extract", {})
        h_code = agg.get(h, {}).get("code_gen", {})
        html_rates.append(h_html.get("rate", np.nan))
        code_rates.append(h_code.get("rate", np.nan))
        html_wall.append(h_html.get("wall_total_s", 0) if h_html else 0)
        code_wall.append(h_code.get("wall_total_s", 0) if h_code else 0)

    html_rates_a = np.array(html_rates, dtype=float)
    code_rates_a = np.array(code_rates, dtype=float)

    ax_top.barh(
        y_pos - bar_h / 2,
        np.where(np.isnan(html_rates_a), 0, html_rates_a),
        bar_h,
        color=GREEN,
        label="HTML extraction (success / 15 trials)",
        edgecolor="white",
    )
    ax_top.barh(
        y_pos + bar_h / 2,
        np.where(np.isnan(code_rates_a), 0, code_rates_a),
        bar_h,
        color=BLUE,
        label="Code generation (success / 15 trials)",
        edgecolor="white",
    )

    for i, (hr, cr) in enumerate(zip(html_rates_a, code_rates_a)):
        if np.isnan(hr):
            ax_top.text(0.005, i - bar_h / 2, "n/a", va="center", ha="left",
                        fontsize=8.5, color=GREY, style="italic")
        else:
            ax_top.text(hr + 0.01, i - bar_h / 2, f"{int(round(hr * 15))}/15",
                        va="center", ha="left", fontsize=9, color=GREEN)
        if np.isnan(cr):
            ax_top.text(0.005, i + bar_h / 2, "n/a", va="center", ha="left",
                        fontsize=8.5, color=GREY, style="italic")
        else:
            ax_top.text(cr + 0.01, i + bar_h / 2, f"{int(round(cr * 15))}/15",
                        va="center", ha="left", fontsize=9, color=BLUE)

    ax_top.set_yticks(y_pos)
    ax_top.set_yticklabels(ORDER, fontsize=10.5)
    ax_top.invert_yaxis()
    ax_top.set_xlim(0, 1.15)
    ax_top.set_xlabel("Success rate", fontsize=10)
    ax_top.set_title(
        "Eight unique harnesses, two task types — success rate per (harness, task)",
        fontsize=12,
        loc="left",
    )
    ax_top.legend(loc="lower right", fontsize=9, frameon=False)
    ax_top.spines["top"].set_visible(False)
    ax_top.spines["right"].set_visible(False)
    ax_top.set_axisbelow(True)
    ax_top.grid(axis="x", linestyle=":", alpha=0.4)

    width = 0.35
    x_pos = np.arange(n_harnesses)
    html_wall_a = np.array([w if w > 0 else np.nan for w in html_wall])
    code_wall_a = np.array([w if w > 0 else np.nan for w in code_wall])

    ax_bot.bar(x_pos - width / 2, np.where(np.isnan(html_wall_a), 0, html_wall_a), width,
               color=GREEN, edgecolor="white", label="HTML extraction")
    ax_bot.bar(x_pos + width / 2, np.where(np.isnan(code_wall_a), 0, code_wall_a), width,
               color=BLUE, edgecolor="white", label="Code generation")

    for i, w in enumerate(html_wall_a):
        if np.isnan(w):
            ax_bot.text(i - width / 2, 30, "n/a", ha="center", va="bottom",
                        fontsize=8, color=GREY, style="italic")
    for i, w in enumerate(code_wall_a):
        if np.isnan(w):
            ax_bot.text(i + width / 2, 30, "n/a", ha="center", va="bottom",
                        fontsize=8, color=GREY, style="italic")

    ax_bot.set_xticks(x_pos)
    ax_bot.set_xticklabels(ORDER, fontsize=9.5, rotation=20, ha="right")
    ax_bot.set_ylabel("Wall-clock total (seconds)", fontsize=10)
    ax_bot.set_title(
        "Wall-clock cost — total seconds across all 15 cells per (harness, task)",
        fontsize=12,
        loc="left",
    )
    ax_bot.legend(loc="upper left", fontsize=9, frameon=False)
    ax_bot.spines["top"].set_visible(False)
    ax_bot.spines["right"].set_visible(False)
    ax_bot.set_axisbelow(True)
    ax_bot.grid(axis="y", linestyle=":", alpha=0.4)

    plt.suptitle(
        "Eight harnesses, both tasks at a glance",
        fontsize=13.5,
        fontweight="bold",
        y=0.995,
        x=0.075,
        ha="left",
    )
    plt.tight_layout(rect=(0, 0, 1, 0.96))

    plt.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
