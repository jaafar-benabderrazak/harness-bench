"""Append-only JSONL trace writer.

Every tool call, every model call, every grader verdict goes to a file keyed by
(harness, task_id, run_id). If a run crashes, the partial trace survives.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import TRACES_DIR

SCHEMA_VERSION = 1


@dataclass
class Tracer:
    harness: str
    task_id: str
    run_id: str
    path: Path = field(init=False)
    _fh: Any = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.path = TRACES_DIR / self.harness / self.task_id / f"{self.run_id}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a", buffering=1, encoding="utf-8")

    def log(self, event_type: str, **payload: Any) -> None:
        record = {
            "schema_version": SCHEMA_VERSION,
            "ts": time.time(),
            "type": event_type,
            **payload,
        }
        self._fh.write(json.dumps(record, default=str) + "\n")
        self._fh.flush()
        os.fsync(self._fh.fileno())

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def __enter__(self) -> "Tracer":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()
