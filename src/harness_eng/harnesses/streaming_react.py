"""Harness: streaming_react.

ReAct-shape loop using STREAMING model responses. On detecting a submit_answer
tool_use start mid-stream, terminates the stream early to save tokens.

LIKELY OLLAMA-INCOMPATIBLE per research § Decisive findings #1 (Ollama issue
#13840 — glm-4.7-flash halts generation after any tool call). Verification
script (scripts/verify_streaming_ollama.py) decides whether this harness is
registered with task_type=['html_extract'] or task_type=[] in HARNESSES_BY_TASK_TYPE.

The harness file lives in the tree REGARDLESS of verification outcome — the
article cites it as 'implemented but unmatrixed' if Ollama-incompatible.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

from ..config import CONFIG
from ..model import ModelCall
from ..tasks.loader import Task
from ..tools import ToolContext, build_tool_list
from ..trace import Tracer
from .base import BASE_ROLE, Harness, ToolAllowlistViolation, _Usage

STREAMING_REACT_TOOLS = ["read_html", "css_select", "extract_text", "submit_answer"]


class StreamingReActHarness(Harness):
    name = "streaming_react"
    TOOL_WHITELIST = frozenset({"read_html", "css_select", "extract_text", "submit_answer"})

    def _execute(
        self,
        task: Task,
        ctx: ToolContext,
        tracer: Tracer,
        usage: _Usage,
    ) -> tuple[dict[str, str] | None, str]:
        system = (
            BASE_ROLE
            + "\n\nYou have tools to inspect the page. Investigate, then call submit_answer. "
            "Responses stream — submit_answer terminates the stream as soon as detected."
        )
        tools = build_tool_list(STREAMING_REACT_TOOLS)
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": self._task_prompt(task)},
        ]
        max_turns = CONFIG.react_max_turns
        for _ in range(max_turns):
            mc = self._step_streaming(system, messages, tools, tracer, usage)
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
                out = self._dispatch_tool(name, args, ctx, tracer, usage)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": tu["id"], "content": out}
                )
            messages.append({"role": "user", "content": tool_results})
        return None, "turn_cap"

    def _step_streaming(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        tracer: Tracer,
        usage: _Usage,
    ) -> ModelCall:
        """Stream a model response. Break early if submit_answer tool_use is detected."""
        if tools:
            passed = {t["name"] for t in tools}
            extra = passed - self.TOOL_WHITELIST
            if extra:
                raise ToolAllowlistViolation(
                    f"Harness '{self.name}' passed tools outside its whitelist: "
                    f"{sorted(extra)}. Whitelist is {sorted(self.TOOL_WHITELIST)}."
                )
            tracer.log("tool_payload", names=sorted(passed))
        tracer.log(
            "model_call",
            system_len=len(system),
            n_messages=len(messages),
            streaming=True,
        )

        if CONFIG.model.backend == "ollama":
            mc = self._stream_ollama(system, messages, tools, tracer)
        else:
            mc = self._stream_anthropic(system, messages, tools, tracer)
        usage.record(mc)
        tracer.log(
            "model_response",
            input_tokens=mc.input_tokens,
            output_tokens=mc.output_tokens,
            usage=mc.usage_raw,
            latency_s=mc.latency_s,
            stop_reason=mc.stop_reason,
            content=mc.content,
        )
        return mc

    def _stream_anthropic(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        tracer: Tracer,
    ) -> ModelCall:
        # Deferred import — module-level would couple this file to the SDK
        # unconditionally and bloat the harness-registry AST seal contract.
        from anthropic import Anthropic  # noqa: PLC0415

        client = Anthropic(max_retries=0)
        kwargs: dict[str, Any] = {
            "model": CONFIG.model.name,
            "max_tokens": CONFIG.model.max_tokens,
            "temperature": CONFIG.model.temperature,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
        t0 = time.perf_counter()
        early_break = False
        with client.messages.stream(**kwargs) as stream:
            for event in stream:
                if (
                    getattr(event, "type", None) == "content_block_start"
                    and getattr(getattr(event, "content_block", None), "type", None) == "tool_use"
                    and getattr(event.content_block, "name", "") == "submit_answer"
                ):
                    tracer.log("streaming_early_termination", reason="submit_answer_detected")
                    early_break = True
                    break
            final = stream.get_final_message()
        latency = time.perf_counter() - t0
        try:
            usage_raw = final.usage.model_dump()
        except AttributeError:
            usage_raw = dict(final.usage.__dict__)
        usage_raw["early_break"] = early_break
        return ModelCall(
            input_tokens=final.usage.input_tokens,
            output_tokens=final.usage.output_tokens,
            latency_s=latency,
            stop_reason=(final.stop_reason or "") + (" (early_break)" if early_break else ""),
            content=[b.model_dump() for b in final.content],
            usage_raw=usage_raw,
        )

    def _stream_ollama(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        tracer: Tracer,
    ) -> ModelCall:
        # Deferred import — module-level would couple to ollama unconditionally.
        # NOTE: glm-4.7-flash likely halts after first tool call (issue #13840).
        # The verification script decides whether this harness is registered.
        import ollama  # noqa: PLC0415

        # Reuse the existing Anthropic<->Ollama shape translation. These are
        # private helpers in model.py; importing them here keeps the streaming
        # path consistent with the non-streaming path's wire format.
        from ..model import _to_ollama_messages, _to_ollama_tools  # noqa: PLC0415

        om = _to_ollama_messages(system, messages)
        ot = _to_ollama_tools(tools)
        options: dict[str, Any] = {
            "temperature": CONFIG.model.temperature,
            "num_predict": CONFIG.model.max_tokens,
        }
        t0 = time.perf_counter()
        kwargs: dict[str, Any] = {
            "model": CONFIG.model.name,
            "messages": om,
            "options": options,
            "stream": True,
        }
        if ot:
            kwargs["tools"] = ot

        # Aggregate streamed chunks. Break early if a submit_answer tool_call
        # is detected mid-stream.
        text_parts: list[str] = []
        tool_calls_acc: list[Any] = []
        early_break = False
        last_chunk = None
        for chunk in ollama.chat(**kwargs):
            last_chunk = chunk
            msg = chunk.message
            if getattr(msg, "content", None):
                text_parts.append(msg.content)
            tcs = getattr(msg, "tool_calls", None) or []
            for tc in tcs:
                tool_calls_acc.append(tc)
                if getattr(tc, "function", None) and tc.function.name == "submit_answer":
                    tracer.log("streaming_early_termination", reason="submit_answer_detected")
                    early_break = True
                    break
            if early_break:
                break

        latency = time.perf_counter() - t0
        # Build content blocks Anthropic-shape from accumulated text + tool_calls.
        content_blocks: list[dict[str, Any]] = []
        text = "".join(text_parts)
        if text:
            content_blocks.append({"type": "text", "text": text})
        for tc in tool_calls_acc:
            args = tc.function.arguments
            if not isinstance(args, dict):
                args = dict(args) if args else {}
            content_blocks.append(
                {
                    "type": "tool_use",
                    "id": f"tu_{uuid.uuid4().hex[:10]}",
                    "name": tc.function.name,
                    "input": args,
                }
            )
        stop_reason = ("tool_use" if tool_calls_acc else "end_turn") + (
            " (early_break)" if early_break else ""
        )
        # last_chunk has the final token counts when stream completes naturally;
        # if we broke early, counts may be partial — record what we have.
        input_tokens = (getattr(last_chunk, "prompt_eval_count", 0) or 0) if last_chunk else 0
        output_tokens = (getattr(last_chunk, "eval_count", 0) or 0) if last_chunk else 0
        return ModelCall(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_s=latency,
            stop_reason=stop_reason,
            content=content_blocks,
            usage_raw={"backend": "ollama", "stream": True, "early_break": early_break},
        )
