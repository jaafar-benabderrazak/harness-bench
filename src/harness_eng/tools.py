"""Tool definitions shared across harnesses.

Implementations are shared. Harnesses choose *which subset* to expose by name.
The minimal harness deliberately omits `read_html` — the model must navigate
via selectors rather than dump raw HTML into context.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from bs4 import BeautifulSoup

from .config import FIXTURES_DIR


@dataclass
class ToolContext:
    html_path: Path
    _html_cache: str | None = None

    def html(self) -> str:
        if self._html_cache is None:
            self._html_cache = (FIXTURES_DIR / self.html_path).read_text(encoding="utf-8")
        return self._html_cache


def _tool_read_html(ctx: ToolContext, **_: Any) -> str:
    return ctx.html()


def _tool_css_select(ctx: ToolContext, selector: str, **_: Any) -> str:
    soup = BeautifulSoup(ctx.html(), "lxml")
    matches = soup.select(selector)
    if not matches:
        return "NO_MATCH"
    # Return up to 10 matches, stripped.
    return "\n---\n".join(m.get_text(" ", strip=True) for m in matches[:10])


def _tool_extract_text(ctx: ToolContext, **_: Any) -> str:
    soup = BeautifulSoup(ctx.html(), "lxml")
    text = soup.get_text(" ", strip=True)
    return text[:4000]


# submit_answer is special — it's not a "tool" that returns data to the model,
# it's the termination signal. The harness watches for it and ends the run.
SUBMIT_ANSWER_TOOL = "submit_answer"


TOOL_IMPLS: dict[str, Callable[..., str]] = {
    "read_html": _tool_read_html,
    "css_select": _tool_css_select,
    "extract_text": _tool_extract_text,
}


TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "read_html": {
        "name": "read_html",
        "description": "Return the full raw HTML for the current task. Use sparingly; it is long.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    "css_select": {
        "name": "css_select",
        "description": "Run a CSS selector against the page and return the text of up to 10 matches, '---'-separated. Returns 'NO_MATCH' if nothing matches.",
        "input_schema": {
            "type": "object",
            "properties": {"selector": {"type": "string"}},
            "required": ["selector"],
        },
    },
    "extract_text": {
        "name": "extract_text",
        "description": "Return the visible text of the page, truncated to 4000 chars.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    "submit_answer": {
        "name": "submit_answer",
        "description": "Submit the final answer as a JSON object mapping field names to extracted string values. This ends the task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fields": {
                    "type": "object",
                    "description": "Mapping of field name to extracted value (string).",
                    "additionalProperties": {"type": "string"},
                }
            },
            "required": ["fields"],
        },
    },
}


def build_tool_list(names: list[str]) -> list[dict[str, Any]]:
    """Build the Anthropic `tools` list from a subset of tool names."""
    return [TOOL_SCHEMAS[n] for n in names]


def dispatch(name: str, ctx: ToolContext, **args: Any) -> str:
    if name not in TOOL_IMPLS:
        return f"ERROR: unknown tool {name}"
    try:
        return TOOL_IMPLS[name](ctx, **args)
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"
