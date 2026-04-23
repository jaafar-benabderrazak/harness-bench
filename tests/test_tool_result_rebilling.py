"""Regression: tool_result tokens are re-billed on each subsequent turn's input_tokens.

Anthropic's API bills a prior turn's tool_result block as input on the NEXT turn.
A multi-turn harness keeping history must see input_tokens grow with history length.
This test pins the re-billing shape using a fake model.call whose input_tokens
scales with message history — NOT a constant stub, which would prove nothing.
"""
from __future__ import annotations

from harness_eng import model as model_module
from harness_eng.model import ModelCall


def _fake_call_factory(tool_out_tokens: int = 1000):
    def fake_call(system, messages, tools=None):
        n_prior_tool_results = sum(
            1
            for m in messages
            if isinstance(m.get("content"), list)
            and any(
                isinstance(b, dict) and b.get("type") == "tool_result"
                for b in m["content"]
            )
        )
        input_tokens = 500 + tool_out_tokens * n_prior_tool_results
        return ModelCall(
            input_tokens=input_tokens,
            output_tokens=50,
            latency_s=0.01,
            stop_reason="tool_use",
            content=[],
            usage_raw={"input_tokens": input_tokens, "output_tokens": 50},
        )

    return fake_call


def test_tool_result_tokens_accumulate_across_turns(monkeypatch):
    """Cumulative input_tokens over 3 turns grows linearly with tool_result history."""
    monkeypatch.setattr(model_module, "call", _fake_call_factory(tool_out_tokens=1000))

    mc1 = model_module.call("sys", [{"role": "user", "content": "go"}])

    msgs_t2 = [
        {"role": "user", "content": "go"},
        {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": "t1", "name": "x", "input": {}}],
        },
        {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "x" * 100}],
        },
    ]
    mc2 = model_module.call("sys", msgs_t2)

    msgs_t3 = msgs_t2 + [
        {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": "t2", "name": "x", "input": {}}],
        },
        {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "t2", "content": "y" * 100}],
        },
    ]
    mc3 = model_module.call("sys", msgs_t3)

    cumulative = mc1.input_tokens + mc2.input_tokens + mc3.input_tokens
    assert cumulative == 4500, f"cumulative input_tokens wrong: {cumulative}"

    assert mc2.input_tokens > mc1.input_tokens
    assert mc3.input_tokens > mc2.input_tokens

    assert mc3.input_tokens - mc2.input_tokens >= 900
    assert mc2.input_tokens - mc1.input_tokens >= 900
