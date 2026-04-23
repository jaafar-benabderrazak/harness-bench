"""Regression tests for trace schema v1 and crash-survival semantics."""
from __future__ import annotations

import json

from harness_eng.trace import SCHEMA_VERSION, Tracer


def test_every_record_has_schema_version(tmp_path, monkeypatch):
    """Every record written by Tracer.log carries schema_version=SCHEMA_VERSION."""
    monkeypatch.setattr("harness_eng.trace.TRACES_DIR", tmp_path)
    with Tracer("test_harness", "task_01", "runid123") as t:
        t.log("run_start", foo=1)
        t.log("model_call", n_messages=2)
        t.log("run_end", ok=True)

    trace_file = tmp_path / "test_harness" / "task_01" / "runid123.jsonl"
    records = [
        json.loads(line)
        for line in trace_file.read_text(encoding="utf-8").splitlines()
    ]
    assert len(records) == 3
    for r in records:
        assert r["schema_version"] == SCHEMA_VERSION
        assert "ts" in r
        assert "type" in r
    assert [r["type"] for r in records] == ["run_start", "model_call", "run_end"]


def test_partial_trace_parseable_after_truncation(tmp_path, monkeypatch):
    """Simulate crash mid-write: truncate the file mid-last-line; prior records parse."""
    monkeypatch.setattr("harness_eng.trace.TRACES_DIR", tmp_path)
    with Tracer("h", "t", "r") as t:
        t.log("run_start")
        t.log("model_call", n=1)
        t.log("model_call", n=2)

    trace_file = tmp_path / "h" / "t" / "r.jsonl"
    raw = trace_file.read_bytes()
    trace_file.write_bytes(raw[:-5])

    good_lines = []
    for line in trace_file.read_text(encoding="utf-8").splitlines():
        try:
            good_lines.append(json.loads(line))
        except json.JSONDecodeError:
            break
    assert len(good_lines) >= 2
    assert good_lines[0]["type"] == "run_start"
    for r in good_lines:
        assert r["schema_version"] == SCHEMA_VERSION
