"""Deterministic grader: normalized exact match per field.

Per-field score is 0 or 1. Task score is per-field mean. A task is 'success'
only if every field matches (all-or-nothing), but per-field accuracy is kept
for the chart.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class GraderResult:
    per_field: dict[str, bool]
    field_accuracy: float
    success: bool  # all fields correct


_WS = re.compile(r"\s+")


def _norm(s: str) -> str:
    return _WS.sub(" ", s.strip().lower())


def grade(predicted: dict[str, str] | None, expected: dict[str, str]) -> GraderResult:
    predicted = predicted or {}
    per_field: dict[str, bool] = {}
    for key, expected_val in expected.items():
        got = predicted.get(key, "")
        per_field[key] = _norm(str(got)) == _norm(str(expected_val))
    correct = sum(per_field.values())
    total = max(len(per_field), 1)
    return GraderResult(
        per_field=per_field,
        field_accuracy=correct / total,
        success=all(per_field.values()),
    )
