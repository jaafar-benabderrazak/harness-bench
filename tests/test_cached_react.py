"""Control-flow tests: cache hits within a cell + cache does NOT leak across cells."""
from __future__ import annotations

from harness_eng.harnesses import base as base_module
from harness_eng.harnesses.cached_react import CachedReActHarness
from harness_eng.model import ModelCall
from harness_eng.tasks.loader import Task


def _build_task(html_path: str = "") -> Task:
    return Task(
        id="t1",
        type="html_extract",
        description="x",
        fields=["title"],
        expected={"title": "X"},
        html_path=html_path,
        test_code="",
        signature="",
    )


def test_cache_hit_on_repeated_selector_within_cell(monkeypatch):
    """First call: css_select(.a) — dispatched. Second call: css_select(.a) — cache hit."""
    call_n = {"n": 0}

    def fake_call(system, messages, tools=None, *, temperature=None):
        call_n["n"] += 1
        if call_n["n"] in (1, 2):
            return ModelCall(
                1,
                1,
                0.0,
                "tool_use",
                content=[
                    {
                        "type": "tool_use",
                        "id": f"tu_{call_n['n']}",
                        "name": "css_select",
                        "input": {"selector": ".a"},
                    }
                ],
                usage_raw={},
            )
        return ModelCall(
            1,
            1,
            0.0,
            "tool_use",
            content=[
                {
                    "type": "tool_use",
                    "id": "submit_id",
                    "name": "submit_answer",
                    "input": {"fields": {"title": "X"}},
                }
            ],
            usage_raw={},
        )

    monkeypatch.setattr(base_module, "model_call", fake_call)
    dispatched: list[str] = []
    monkeypatch.setattr(
        "harness_eng.harnesses.cached_react.Harness._dispatch_tool",
        lambda self, name, args, ctx, tracer, usage: (
            dispatched.append(args.get("selector", name)),
            "match!",
        )[1],
        raising=False,
    )
    # Force ctx.html() to return a fixed string so html_hash is stable
    from harness_eng import tools as tools_mod

    monkeypatch.setattr(tools_mod.ToolContext, "html", lambda self: "<html></html>")

    harness = CachedReActHarness()
    task = _build_task(html_path="any.html")
    cache_hit_events: list[bool] = []
    from harness_eng import trace as trace_mod

    orig = trace_mod.Tracer.log

    def capture(self, ev_type, **kw):
        if ev_type == "tool_call":
            cache_hit_events.append(kw.get("cache_hit", False))
        return orig(self, ev_type, **kw)

    monkeypatch.setattr(trace_mod.Tracer, "log", capture)

    harness.run(task, run_id="t")
    # _dispatch_tool was called only ONCE for the selector — the second
    # css_select model call hit the cache and never reached _dispatch_tool.
    assert dispatched == [".a"], f"expected one dispatch, got {dispatched}"
    # Exactly one tool_call trace event was emitted from the cache-hit branch
    # (the dispatch branch was monkeypatched out, so the dispatch tool_call
    # never fires through the real Harness._dispatch_tool here).
    assert any(hit is True for hit in cache_hit_events), (
        f"expected at least one cache_hit=True tool_call event, got {cache_hit_events}"
    )


def test_cache_does_not_leak_across_cells(monkeypatch):
    """Re-running the harness with same selector should re-dispatch (fresh cache per _execute call)."""
    call_n = {"n": 0}

    def fake_call(system, messages, tools=None, *, temperature=None):
        call_n["n"] += 1
        if call_n["n"] % 2 == 1:
            return ModelCall(
                1,
                1,
                0.0,
                "tool_use",
                content=[
                    {
                        "type": "tool_use",
                        "id": f"x{call_n['n']}",
                        "name": "css_select",
                        "input": {"selector": ".a"},
                    }
                ],
                usage_raw={},
            )
        return ModelCall(
            1,
            1,
            0.0,
            "tool_use",
            content=[
                {
                    "type": "tool_use",
                    "id": "s",
                    "name": "submit_answer",
                    "input": {"fields": {"title": "X"}},
                }
            ],
            usage_raw={},
        )

    monkeypatch.setattr(base_module, "model_call", fake_call)
    dispatched: list[str] = []
    monkeypatch.setattr(
        "harness_eng.harnesses.cached_react.Harness._dispatch_tool",
        lambda self, name, args, ctx, tracer, usage: (
            dispatched.append(args.get("selector", name)),
            "match!",
        )[1],
        raising=False,
    )
    from harness_eng import tools as tools_mod

    monkeypatch.setattr(tools_mod.ToolContext, "html", lambda self: "<html></html>")

    harness = CachedReActHarness()  # ONE instance — same as runner does
    task = _build_task(html_path="any.html")
    harness.run(task, run_id="cell-1")
    harness.run(task, run_id="cell-2")
    # If cache leaked, dispatched would have ['.a'] only; if it didn't, ['.a', '.a']
    assert dispatched == [".a", ".a"], (
        f"cache leaked across cells (dispatched={dispatched}). "
        f"Cache MUST be a local in _execute."
    )


def test_cache_is_not_a_self_attribute():
    """Static guarantee: harness instance has no `cache` attribute."""
    h = CachedReActHarness()
    assert not hasattr(h, "cache"), (
        "cache must be a local in _execute, not on self (would leak across cells)"
    )
    assert not hasattr(h, "_cache"), "cache must be a local in _execute, not on self"
