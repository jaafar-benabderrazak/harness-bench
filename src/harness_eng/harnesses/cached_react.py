"""Harness: cached_react.

Standard ReAct loop with a cell-scoped (html_hash, selector) result cache.
The cache is a LOCAL variable in _execute (NOT an instance attribute) so it
dies with the method scope and cannot leak across cells. Per CONTEXT decision #8.

Article framing: shows what react would cost if tool calls were free.
Within-cell amortization only — no cross-cell or cross-seed cost savings.
"""
from __future__ import annotations

import hashlib
from typing import Any

from ..config import CONFIG
from ..tasks.loader import Task
from ..tools import ToolContext, build_tool_list
from ..trace import Tracer
from .base import BASE_ROLE, Harness, _Usage

CACHED_REACT_TOOLS = ["read_html", "css_select", "extract_text", "submit_answer"]


class CachedReActHarness(Harness):
    name = "cached_react"
    TOOL_WHITELIST = frozenset({"read_html", "css_select", "extract_text", "submit_answer"})

    def _execute(
        self,
        task: Task,
        ctx: ToolContext,
        tracer: Tracer,
        usage: _Usage,
    ) -> tuple[dict[str, str] | None, str]:
        # CELL-SCOPED CACHE — local variable. Do NOT move this onto the
        # harness instance. runner.py reuses harness instances across cells;
        # an instance attribute would leak selector results across cells and
        # break seed independence (see CONTEXT decision #8).
        cache: dict[tuple[str, str], str] = {}
        html_hash = (
            hashlib.sha256(ctx.html().encode("utf-8")).hexdigest()[:16]
            if task.html_path
            else ""
        )

        system = (
            BASE_ROLE
            + "\n\nYou have tools to inspect the page. Repeated identical (selector) "
            "calls within this task are answered from cache for speed."
        )
        tools = build_tool_list(CACHED_REACT_TOOLS)
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": self._task_prompt(task)},
        ]
        max_turns = CONFIG.react_max_turns
        for _ in range(max_turns):
            mc = self._step_model(system, messages, tools, tracer, usage)
            messages.append({"role": "assistant", "content": mc.content})
            tool_uses = self._tool_uses(mc.content)
            if not tool_uses:
                return None, "no_submit"
            tool_results: list[dict[str, Any]] = []
            for tu in tool_uses:
                name = tu["name"]
                args = tu.get("input", {}) or {}
                if name == "submit_answer":
                    if "code" in args:
                        return {"code": args["code"]}, "submitted"
                    fields = args.get("fields", {})
                    return {k: str(v) for k, v in fields.items()}, "submitted"
                # Cache lookup ONLY for css_select — other tools are deterministic but cheap
                if name == "css_select":
                    sel = args.get("selector", "")
                    key = (html_hash, sel)
                    if key in cache:
                        out = cache[key]
                        # Count cache hits as tool_calls (model still emitted the call)
                        # but mark cache_hit=True in trace so analysis can split.
                        tracer.log("tool_call", name=name, args=args, cache_hit=True)
                        usage.tool_calls += 1
                        tracer.log(
                            "tool_result",
                            name=name,
                            output_len=len(out),
                            cache_hit=True,
                        )
                    else:
                        out = self._dispatch_tool(name, args, ctx, tracer, usage)
                        cache[key] = out
                else:
                    out = self._dispatch_tool(name, args, ctx, tracer, usage)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": tu["id"], "content": out}
                )
            messages.append({"role": "user", "content": tool_results})
        return None, "turn_cap"
