"""Harness registry. Keep the order here aligned with the article."""
from __future__ import annotations

from .base import Harness, HarnessResult
from .minimal import MinimalHarness
from .plan_execute import PlanExecuteHarness
from .react import ReActHarness
from .reflexion import ReflexionHarness
from .single_shot import SingleShotHarness

HARNESSES: dict[str, type[Harness]] = {
    "single_shot": SingleShotHarness,
    "react": ReActHarness,
    "plan_execute": PlanExecuteHarness,
    "reflexion": ReflexionHarness,
    "minimal": MinimalHarness,
}

__all__ = ["Harness", "HarnessResult", "HARNESSES"]
