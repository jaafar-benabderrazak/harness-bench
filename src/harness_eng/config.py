"""Frozen experiment configuration. Single source of truth for the model and limits.

Every harness imports from here. Nothing else imports anthropic config directly.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
TRACES_DIR = ROOT / "traces"
RESULTS_DIR = ROOT / "results"
TASKS_DIR = Path(__file__).resolve().parent / "tasks"
FIXTURES_DIR = TASKS_DIR / "fixtures"
TASKS_FILE = TASKS_DIR / "tasks.jsonl"


@dataclass(frozen=True)
class ModelConfig:
    name: str
    max_tokens: int
    temperature: float
    backend: str  # "anthropic" or "ollama"


@dataclass(frozen=True)
class ExperimentConfig:
    model: ModelConfig
    react_max_turns: int = 12
    minimal_max_turns: int = 12
    minimal_prune_every: int = 4
    reflexion_max_retries: int = 1
    plan_max_steps: int = 8


def load_config() -> ExperimentConfig:
    backend = os.getenv("HARNESS_BACKEND", "ollama").lower()
    default_model = {
        "anthropic": "claude-sonnet-4-6",
        "ollama": "mistral:7b",
    }.get(backend, "mistral:7b")
    return ExperimentConfig(
        model=ModelConfig(
            name=os.getenv("HARNESS_MODEL", default_model),
            max_tokens=int(os.getenv("HARNESS_MAX_TOKENS", "2048")),
            temperature=float(os.getenv("HARNESS_TEMPERATURE", "0.0")),
            backend=backend,
        ),
    )


CONFIG = load_config()
