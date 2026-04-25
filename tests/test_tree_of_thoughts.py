"""Control-flow test for tree_of_thoughts: 3 candidates proposed, deterministic scoring, winner used downstream."""
from __future__ import annotations

import pytest

from harness_eng.harnesses import base as base_module
from harness_eng.harnesses.tree_of_thoughts import (
    TreeOfThoughtsHarness,
    _score_candidate,
)
from harness_eng.model import ModelCall
from harness_eng.tasks.loader import Task


def test_score_candidate_zero_for_empty():
    assert _score_candidate([]) == 0.0


def test_score_candidate_prefers_more_specific():
    # 3 short matches > 1 long match
    assert _score_candidate(["abc", "def", "ghi"]) > _score_candidate(["a" * 100])


def test_tree_of_thoughts_proposes_three_then_submits(monkeypatch):
    """First call: 3 candidates as text. Second call: submit_answer."""
    seen: list[dict] = []

    def fake_call(system, messages, tools=None, *, temperature=None):
        seen.append({"system": system, "tools": tools})
        if len(seen) == 1:
            # toolless propose call
            return ModelCall(
                input_tokens=1,
                output_tokens=1,
                latency_s=0.0,
                stop_reason="end_turn",
                content=[{"type": "text", "text": "1. h1\n2. .title\n3. #main h2"}],
                usage_raw={},
            )
        # second call -> submit
        return ModelCall(
            input_tokens=1,
            output_tokens=1,
            latency_s=0.0,
            stop_reason="end_turn",
            content=[
                {
                    "type": "tool_use",
                    "id": "tu_1",
                    "name": "submit_answer",
                    "input": {"fields": {"title": "X"}},
                }
            ],
            usage_raw={},
        )

    monkeypatch.setattr(base_module, "model_call", fake_call)
    # Stub dispatch so .title returns 2 short matches and others NO_MATCH
    import harness_eng.harnesses.tree_of_thoughts as tot_mod

    monkeypatch.setattr(
        tot_mod,
        "dispatch",
        lambda name, ctx, **kw: "match1\n---\nmatch2"
        if kw.get("selector") == ".title"
        else "NO_MATCH",
    )

    harness = TreeOfThoughtsHarness()
    task = Task(
        id="t1",
        type="html_extract",
        description="extract",
        fields=["title"],
        expected={"title": "X"},
        html_path="",
        test_code="",
        signature="",
    )
    result = harness.run(task, run_id="t")
    assert result.stop_reason == "submitted"
    assert result.predicted == {"title": "X"}
    assert len(seen) == 2
    # First call had no tools (propose phase)
    assert seen[0]["tools"] is None
    # Second call had tools (submit phase)
    assert seen[1]["tools"] is not None
