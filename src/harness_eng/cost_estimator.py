"""Dry-run cost estimator. Run BEFORE the full matrix.

Projects tokens-per-cell from an empirical baseline (tiny warmup run) and
multiplies out across the matrix. Prints projected USD with a 2x safety margin.
"""
from __future__ import annotations

from dataclasses import dataclass

from .config import CONFIG
from .pricing import PRICING, cost_usd


@dataclass
class CellEstimate:
    harness: str
    in_tokens: int
    out_tokens: int


# Rough per-cell estimates based on harness shape. Update from a pilot run.
# input includes full HTML for single_shot, larger for react+plan_execute due
# to accumulated tool history, smaller for minimal (pruned).
DEFAULT_ESTIMATES: list[CellEstimate] = [
    CellEstimate("single_shot",  in_tokens=2_500,  out_tokens=250),
    CellEstimate("react",        in_tokens=7_500,  out_tokens=600),
    CellEstimate("plan_execute", in_tokens=8_500,  out_tokens=700),
    CellEstimate("reflexion",    in_tokens=14_000, out_tokens=1_100),
    CellEstimate("minimal",      in_tokens=4_000,  out_tokens=400),
]


def estimate_matrix(
    n_tasks: int,
    n_seeds: int = 1,
    safety: float = 2.0,
    estimates: list[CellEstimate] | None = None,
    model: str | None = None,
) -> dict:
    estimates = estimates or DEFAULT_ESTIMATES
    model = model or CONFIG.model.name
    inp, outp = PRICING.get(model, (3.0, 15.0))
    rows = []
    total = 0.0
    for ce in estimates:
        cells = n_tasks * n_seeds
        in_tokens = ce.in_tokens * cells
        out_tokens = ce.out_tokens * cells
        cell_cost = cost_usd(model, in_tokens, out_tokens)
        rows.append({
            "harness": ce.harness,
            "cells": cells,
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "cost_usd": cell_cost,
        })
        total += cell_cost
    return {
        "model": model,
        "price_per_mtok": (inp, outp),
        "n_tasks": n_tasks,
        "n_seeds": n_seeds,
        "rows": rows,
        "total_usd": total,
        "total_usd_with_safety": total * safety,
        "safety": safety,
    }


def format_estimate(est: dict) -> str:
    lines = [
        f"Cost estimate for model={est['model']} "
        f"({est['price_per_mtok'][0]}$/Mtok in, {est['price_per_mtok'][1]}$/Mtok out)",
        f"Matrix: {est['n_tasks']} tasks x {est['n_seeds']} seeds = {est['n_tasks']*est['n_seeds']} cells per harness",
        "",
        f"{'harness':<14} {'cells':>6} {'in_tok':>10} {'out_tok':>10} {'usd':>8}",
    ]
    for r in est["rows"]:
        lines.append(
            f"{r['harness']:<14} {r['cells']:>6} {r['input_tokens']:>10} "
            f"{r['output_tokens']:>10} {r['cost_usd']:>8.3f}"
        )
    lines.append("")
    lines.append(f"Projected total: ${est['total_usd']:.2f}")
    lines.append(f"With {est['safety']:.1f}x safety margin: ${est['total_usd_with_safety']:.2f}")
    return "\n".join(lines)
