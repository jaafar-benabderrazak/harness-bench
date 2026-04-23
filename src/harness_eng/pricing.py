"""Anthropic pricing table for cost accounting.

These numbers are *estimates* for comparison across harnesses — the ratios
matter more than the absolute dollar figures. Update if pricing changes.
"""
from __future__ import annotations

# USD per 1M tokens. Update as Anthropic publishes new prices.
PRICING: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6": (3.0, 15.0),   # (input, output) per 1M
    "claude-opus-4-7":    (15.0, 75.0),
    "claude-haiku-4-5":   (1.0, 5.0),
}


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in PRICING:
        return 0.0
    inp, outp = PRICING[model]
    return (input_tokens / 1_000_000) * inp + (output_tokens / 1_000_000) * outp
