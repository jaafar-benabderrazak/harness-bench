"""Pilot: run all five harnesses on a single task to sanity-check the plumbing.

Use this before committing API spend on the full matrix.
"""
from __future__ import annotations

import sys

from harness_eng.harnesses import HARNESSES
from harness_eng.runner import run_matrix
from harness_eng.tasks.loader import load_tasks


def main() -> int:
    tasks = load_tasks()[:1]
    out = run_matrix(list(HARNESSES.keys()), tasks=tasks, seeds=1)
    print(f"\nPilot written to: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
