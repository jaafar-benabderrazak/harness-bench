"""Single point of contact with the model. All harnesses route through call().

Any harness that imports anthropic directly is a bug. The whole point of the
experiment is that this module is frozen while the harnesses change.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from .config import CONFIG

_client: Any = None


def _get_client() -> Any:
    global _client
    if _client is None:
        # Deferred import so the module is importable (e.g. for tests) without
        # the SDK installed. Only the runtime path calls this.
        from anthropic import Anthropic
        _client = Anthropic()
    return _client


@dataclass
class ModelCall:
    input_tokens: int
    output_tokens: int
    latency_s: float
    stop_reason: str
    content: list[dict[str, Any]]


def call(
    system: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
) -> ModelCall:
    """Single entry point. Returns normalized response + usage."""
    client = _get_client()
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
    resp = client.messages.create(**kwargs)
    latency = time.perf_counter() - t0

    return ModelCall(
        input_tokens=resp.usage.input_tokens,
        output_tokens=resp.usage.output_tokens,
        latency_s=latency,
        stop_reason=resp.stop_reason or "",
        content=[b.model_dump() for b in resp.content],
    )
