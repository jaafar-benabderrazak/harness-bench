"""Control-flow tests: program_aided uses run_python before submit; harness rejects html_extract tasks."""
from harness_eng.harnesses import base as base_module
from harness_eng.harnesses.program_aided import ProgramAidedHarness
from harness_eng.model import ModelCall
from harness_eng.tasks.loader import Task


def test_program_aided_uses_run_python_before_submit(monkeypatch):
    """First call: run_python. Second call: submit_answer."""
    call_n = {"n": 0}

    def fake_call(system, messages, tools=None, **_kw):
        call_n["n"] += 1
        if call_n["n"] == 1:
            return ModelCall(1, 1, 0.0, "tool_use",
                content=[{"type": "tool_use", "id": "tu1", "name": "run_python",
                          "input": {"code": "print(sorted([3,1,2]))"}}],
                usage_raw={})
        return ModelCall(1, 1, 0.0, "tool_use",
            content=[{"type": "tool_use", "id": "tu2", "name": "submit_answer",
                      "input": {"code": "def f(x): return sorted(x)"}}],
            usage_raw={})

    monkeypatch.setattr(base_module, "model_call", fake_call)
    captured_events: list[str] = []
    from harness_eng import trace as trace_mod
    orig = trace_mod.Tracer.log
    monkeypatch.setattr(trace_mod.Tracer, "log",
        lambda self, ev_type, **kw: (captured_events.append(ev_type), orig(self, ev_type, **kw))[1])

    harness = ProgramAidedHarness()
    task = Task(id="t1", type="code_gen", description="sort",
                fields=[], expected={}, html_path="",
                test_code="def test_x(): assert f([3,1,2]) == [1,2,3]",
                signature="def f(x): pass")
    result = harness.run(task, run_id="t")
    assert result.stop_reason == "submitted"
    assert "program_aided_run_python" in captured_events, \
        "expected program_aided_run_python event; got " + str(set(captured_events))


def test_program_aided_rejects_html_task(monkeypatch):
    """If invoked on html_extract, returns no_submit cleanly (no model call)."""
    monkeypatch.setattr(base_module, "model_call",
        lambda *a, **kw: ModelCall(0, 0, 0.0, "end_turn", content=[], usage_raw={}))
    harness = ProgramAidedHarness()
    task = Task(id="t1", type="html_extract", description="x",
                fields=["title"], expected={"title": "X"},
                html_path="", test_code="", signature="")
    result = harness.run(task, run_id="t")
    assert result.stop_reason == "no_submit"


def test_program_aided_whitelist_only_run_python_and_submit():
    """TOOL_WHITELIST is exactly {run_python, submit_answer} — no css_select etc."""
    assert ProgramAidedHarness.TOOL_WHITELIST == frozenset({"run_python", "submit_answer"})
