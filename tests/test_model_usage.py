"""Regression: Anthropic client constructed with max_retries=0 and ModelCall.usage_raw populated."""
from __future__ import annotations

import sys
import types

from harness_eng import model as model_module


def test_client_constructed_with_max_retries_zero(monkeypatch):
    """When _get_client instantiates the client, it passes max_retries=0."""
    captured: dict = {}

    class FakeAnthropic:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    fake_mod = types.ModuleType("anthropic")
    fake_mod.Anthropic = FakeAnthropic
    monkeypatch.setitem(sys.modules, "anthropic", fake_mod)
    monkeypatch.setattr(model_module, "_client", None)
    model_module._get_client()
    assert captured.get("max_retries") == 0, f"expected max_retries=0, got {captured!r}"


def test_usage_raw_populated(monkeypatch):
    """ModelCall.usage_raw contains every field returned by resp.usage.model_dump()."""
    class FakeUsage:
        input_tokens = 100
        output_tokens = 50

        def model_dump(self):
            return {
                "input_tokens": 100,
                "output_tokens": 50,
                "cache_read_input_tokens": 10,
                "cache_creation_input_tokens": 5,
            }

    class FakeContent:
        def model_dump(self):
            return {"type": "text", "text": "ok"}

    class FakeResp:
        usage = FakeUsage()
        stop_reason = "end_turn"
        content = [FakeContent()]

    class FakeMessages:
        def create(self, **_kw):
            return FakeResp()

    class FakeClient:
        messages = FakeMessages()

    monkeypatch.setattr(model_module, "_client", FakeClient())
    mc = model_module.call(system="sys", messages=[{"role": "user", "content": "hi"}])
    assert mc.usage_raw == {
        "input_tokens": 100,
        "output_tokens": 50,
        "cache_read_input_tokens": 10,
        "cache_creation_input_tokens": 5,
    }
    assert mc.input_tokens == 100
    assert mc.output_tokens == 50
