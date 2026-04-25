"""Control-flow tests for streaming_react harness.

Mocked: model streaming is faked at the _step_streaming boundary so the harness
loop body is exercised without an actual SDK call. Asserts the harness consumes
a streamed submit_answer and terminates the run with stop_reason='submitted'.

Whitelist + AST-shape contracts are also tested here. Note: the global AST
seal in tests/test_harness_registry.py iterates only registered HARNESSES; this
harness is not registered until plan 08-06 (after the Ollama-compat verify
outcome is read). Until then, the per-module deferred-import check below is
the binding contract.
"""
from __future__ import annotations

from harness_eng.harnesses.streaming_react import StreamingReActHarness
from harness_eng.model import ModelCall
from harness_eng.tasks.loader import Task


def test_streaming_react_terminates_on_submit_detection(monkeypatch):
    """Submit_answer in the streamed response -> stop_reason='submitted', predicted set."""

    def fake_stream(self, system, messages, tools, tracer, usage):
        usage.input_tokens += 1
        usage.output_tokens += 1
        usage.turns += 1
        return ModelCall(
            input_tokens=1,
            output_tokens=1,
            latency_s=0.0,
            stop_reason="tool_use (early_break)",
            content=[
                {
                    "type": "tool_use",
                    "id": "tu1",
                    "name": "submit_answer",
                    "input": {"fields": {"title": "X"}},
                }
            ],
            usage_raw={"early_break": True},
        )

    monkeypatch.setattr(StreamingReActHarness, "_step_streaming", fake_stream)

    harness = StreamingReActHarness()
    task = Task(
        id="t1",
        type="html_extract",
        description="x",
        fields=["title"],
        expected={"title": "X"},
        html_path="",
        test_code="",
        signature="",
    )
    result = harness.run(task, run_id="t")
    assert result.stop_reason == "submitted"
    assert result.predicted == {"title": "X"}


def test_streaming_react_no_tool_use_returns_no_submit(monkeypatch):
    """Streamed response with text-only content -> stop_reason='no_submit'."""

    def fake_stream(self, system, messages, tools, tracer, usage):
        usage.input_tokens += 1
        usage.output_tokens += 1
        usage.turns += 1
        return ModelCall(
            input_tokens=1,
            output_tokens=1,
            latency_s=0.0,
            stop_reason="end_turn",
            content=[{"type": "text", "text": "I think the answer is X."}],
            usage_raw={"early_break": False},
        )

    monkeypatch.setattr(StreamingReActHarness, "_step_streaming", fake_stream)

    harness = StreamingReActHarness()
    task = Task(
        id="t2",
        type="html_extract",
        description="x",
        fields=["title"],
        expected={"title": "X"},
        html_path="",
        test_code="",
        signature="",
    )
    result = harness.run(task, run_id="t")
    assert result.stop_reason == "no_submit"
    assert result.predicted is None


def test_streaming_react_whitelist():
    """Whitelist matches react: read_html / css_select / extract_text / submit_answer."""
    expected = frozenset({"read_html", "css_select", "extract_text", "submit_answer"})
    assert StreamingReActHarness.TOOL_WHITELIST == expected


def test_streaming_react_no_module_level_anthropic_import():
    """Module-level imports must NOT include anthropic; SDK is deferred inside method bodies.

    Inspects the top of the source file (everything before the first 'class' line) so any
    'import anthropic' / 'from anthropic' at module scope is caught while deferred imports
    inside method bodies are tolerated.
    """
    import inspect

    import harness_eng.harnesses.streaming_react as m

    src = inspect.getsource(m)
    head_lines = []
    for line in src.splitlines():
        if line.startswith("class "):
            break
        head_lines.append(line)
    head = "\n".join(head_lines)
    assert "import anthropic" not in head, "anthropic must be imported inside method bodies"
    assert "from anthropic" not in head, "anthropic must be imported inside method bodies"
