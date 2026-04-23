"""Anthropic pricing table for cost accounting.

These numbers are *estimates* for comparison across harnesses — the ratios
matter more than the absolute dollar figures. Update if pricing changes.
"""
from __future__ import annotations

# USD per 1M tokens. Ollama-hosted models cost $0 (electricity only).
PRICING: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-4-7":    (15.0, 75.0),
    "claude-haiku-4-5":   (1.0, 5.0),
    "mistral:7b":         (0.0, 0.0),
    "llama3.1:70b":       (0.0, 0.0),
    "mixtral:8x7b":       (0.0, 0.0),
    "phi3:mini":          (0.0, 0.0),
    "gemma2:27b":         (0.0, 0.0),
    "glm-4.7-flash:latest": (0.0, 0.0),
}


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in PRICING:
        return 0.0
    inp, outp = PRICING[model]
    return (input_tokens / 1_000_000) * inp + (output_tokens / 1_000_000) * outp
