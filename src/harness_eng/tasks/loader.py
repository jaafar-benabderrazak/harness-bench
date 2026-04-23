"""Task loader. A Task is a single HTML-extraction problem."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..config import TASKS_FILE


@dataclass(frozen=True)
class Task:
    id: str
    description: str
    html_path: str  # relative to fixtures dir
    fields: list[str]
    expected: dict[str, str]


def load_tasks(path: Path | None = None) -> list[Task]:
    path = path or TASKS_FILE
    tasks: list[Task] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        obj = json.loads(line)
        tasks.append(
            Task(
                id=obj["id"],
                description=obj["description"],
                html_path=obj["html_path"],
                fields=list(obj["expected"].keys()),
                expected=obj["expected"],
            )
        )
    return tasks
