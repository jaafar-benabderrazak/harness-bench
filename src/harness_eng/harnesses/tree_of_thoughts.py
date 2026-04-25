"""Harness: tree_of_thoughts.

Propose N=3 candidate CSS selectors in a toolless first call, then score each
deterministically (num_matched / mean_text_length) and run a second call with
the winner's match text. Heuristic scoring per CONTEXT decision #2 — no extra
model call to rank, keeps cost comparable to single-shot + 1 turn.
"""
from __future__ import annotations

from typing import Any

from ..tasks.loader import Task
from ..tools import ToolContext, build_tool_list, dispatch
from ..trace import Tracer
from .base import BASE_ROLE, Harness, _Usage

TOT_TOOLS = ["css_select", "submit_answer"]


def _score_candidate(matches: list[str]) -> float:
    """High score = many matches with short text (specific selector). Returns 0 for empty."""
    if not matches:
        return 0.0
    n = len(matches)
    avg_len = sum(len(m) for m in matches) / n
    return n / max(avg_len, 1.0)


class TreeOfThoughtsHarness(Harness):
    name = "tree_of_thoughts"
    TOOL_WHITELIST = frozenset({"css_select", "submit_answer"})

    def _execute(
        self,
        task: Task,
        ctx: ToolContext,
        tracer: Tracer,
        usage: _Usage,
    ) -> tuple[dict[str, str] | None, str]:
        # Stage 1: toolless propose-3 call.
        propose_system = (
            BASE_ROLE
            + "\n\nPropose THREE distinct CSS selectors that target the requested fields. "
            "Return them as a numbered list, one per line, prefixed '1. ', '2. ', '3. '. "
            "Do not call any tools. Do not include explanation."
        )
        propose_msg = [{"role": "user", "content": self._task_prompt(task)}]
        mc = self._step_model(propose_system, propose_msg, None, tracer, usage)
        text = self._text_of(mc.content)
        candidates = _parse_candidates(text)
        tracer.log("tot_candidates", candidates=candidates)
        if not candidates:
            return None, "no_submit"

        # Stage 2: score each candidate deterministically.
        scored: list[tuple[str, float, str]] = []
        for sel in candidates:
            tracer.log("tool_call", name="css_select", args={"selector": sel})
            usage.tool_calls += 1
            out = dispatch("css_select", ctx, selector=sel)
            tracer.log("tool_result", name="css_select", output_len=len(out))
            if out == "NO_MATCH":
                matches: list[str] = []
            else:
                matches = [m for m in out.split("\n---\n") if m]
            score = _score_candidate(matches)
            scored.append((sel, score, out))
        scored.sort(key=lambda x: x[1], reverse=True)
        winner_sel, winner_score, winner_out = scored[0]
        tracer.log("tot_winner", selector=winner_sel, score=winner_score)

        # Stage 3: final submit call with winner's text in context.
        final_system = (
            BASE_ROLE
            + "\n\nUse the provided extraction text to call submit_answer. "
            "Do not call any other tools."
        )
        user = (
            self._task_prompt(task)
            + f"\n\nWinner selector: {winner_sel}\n\nExtraction:\n{winner_out}\n\n"
            "Call submit_answer with the extracted fields."
        )
        tools = build_tool_list(TOT_TOOLS)
        mc2 = self._step_model(
            final_system, [{"role": "user", "content": user}], tools, tracer, usage
        )
        for block in self._tool_uses(mc2.content):
            if block["name"] == "submit_answer":
                inp = block.get("input", {}) or {}
                fields = inp.get("fields", {})
                return {k: str(v) for k, v in fields.items()}, "submitted"
        return None, "no_submit"


def _parse_candidates(text: str) -> list[str]:
    """Parse '1. selector', '2. selector', '3. selector' lines from model output."""
    out: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        for prefix in ("1.", "2.", "3.", "-", "*"):
            if line.startswith(prefix):
                cand = line[len(prefix):].strip()
                # Strip backticks if model wrapped in code formatting
                cand = cand.strip("`")
                if cand:
                    out.append(cand)
                break
    return out[:3]
