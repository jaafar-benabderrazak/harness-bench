"""Harness: program_aided.

Code-gen only. Model uses run_python to execute scratch Python during reasoning
(verify intermediate values, test small cases) before submitting via submit_answer.
Distinct from test_driven: test_driven uses run_tests (pytest grading suite);
program_aided uses run_python (arbitrary script execution as reasoning).

Reference: PaL paper (Gao et al. 2022).
"""
from __future__ import annotations

from typing import Any

from ..config import CONFIG
from ..tasks.loader import Task
from ..tools import ToolContext, build_tool_list
from ..trace import Tracer
from .base import BASE_ROLE, Harness, _Usage

PROGRAM_AIDED_TOOLS = ["run_python", "submit_answer"]


class ProgramAidedHarness(Harness):
    name = "program_aided"
    TOOL_WHITELIST = frozenset({"run_python", "submit_answer"})

    def _execute(self, task: Task, ctx: ToolContext, tracer: Tracer, usage: _Usage) -> tuple[dict[str, str] | None, str]:
        if task.type != "code_gen":
            # This harness is code-gen-only. If somehow invoked on HTML, fail clean.
            return None, "no_submit"
        system = (
            BASE_ROLE
            + "\n\nYou are a code-generation agent. Use the run_python tool to verify "
            "your approach with small test cases BEFORE submitting. Run examples, check "
            "edge cases, then call submit_answer with the final implementation. "
            "You MUST use run_python at least once before submitting."
        )
        user = (
            self._task_prompt(task)
            + f"\n\nFunction signature:\n```python\n{task.signature}\n```\n"
            "Verify your approach with run_python, then submit via submit_answer."
        )
        tools = build_tool_list(PROGRAM_AIDED_TOOLS)
        messages: list[dict[str, Any]] = [{"role": "user", "content": user}]
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
                    return None, "no_submit"
                if name == "run_python":
                    code = args.get("code", "")
                    tracer.log("program_aided_run_python", code_len=len(code))
                out = self._dispatch_tool(name, args, ctx, tracer, usage)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": tu["id"], "content": out}
                )
            messages.append({"role": "user", "content": tool_results})
        return None, "turn_cap"
