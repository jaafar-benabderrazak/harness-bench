"""Harness registry. Keep the order here aligned with the article."""
from __future__ import annotations

from .base import Harness, HarnessResult
from .cached_react import CachedReActHarness
from .chain_of_thought import ChainOfThoughtHarness
from .minimal import MinimalHarness
from .multi_agent import MultiAgentHarness
from .plan_execute import PlanExecuteHarness
from .program_aided import ProgramAidedHarness
from .react import ReActHarness
from .react_with_replan import ReActWithReplanHarness
from .reflexion import ReflexionHarness
from .retry_on_fail import RetryOnFailHarness
from .self_consistency import SelfConsistencyHarness
from .single_shot import SingleShotHarness
from .streaming_react import StreamingReActHarness
from .test_driven import TestDrivenHarness
from .tool_use_with_validation import ToolUseWithValidationHarness
from .tree_of_thoughts import TreeOfThoughtsHarness

HARNESSES: dict[str, type[Harness]] = {
    # HTML-extraction baselines (Phase 1-7)
    "single_shot": SingleShotHarness,
    "react": ReActHarness,
    "plan_execute": PlanExecuteHarness,
    "reflexion": ReflexionHarness,
    "minimal": MinimalHarness,
    # Code-gen baselines (Phase 1-7)
    "chain_of_thought": ChainOfThoughtHarness,
    "test_driven": TestDrivenHarness,
    "retry_on_fail": RetryOnFailHarness,
    # Phase 8: agent-pattern family
    "tree_of_thoughts": TreeOfThoughtsHarness,
    "multi_agent": MultiAgentHarness,
    "react_with_replan": ReActWithReplanHarness,
    "self_consistency": SelfConsistencyHarness,
    "program_aided": ProgramAidedHarness,
    "tool_use_with_validation": ToolUseWithValidationHarness,
    "streaming_react": StreamingReActHarness,
    "cached_react": CachedReActHarness,
}

# Which harnesses apply to each task type. The runner uses this to pick the
# matrix membership for each benchmark.
#
# streaming_react: registered ONLY if Plan 08-05 verification passed
# (see 08-05-VERIFY.md). On Ollama + glm-4.7-flash it almost certainly halts
# post-tool-call (issue #13840), in which case task_type=[] and the harness
# is excluded from the matrix while the file remains in tree.
HARNESSES_BY_TASK_TYPE: dict[str, list[str]] = {
    "html_extract": [
        # Phase 1-7
        "single_shot", "react", "plan_execute", "reflexion", "minimal",
        # Phase 8 HTML additions
        "tree_of_thoughts", "multi_agent", "react_with_replan",
        "self_consistency", "tool_use_with_validation", "cached_react",
        # streaming_react inserted below conditionally
    ],
    "code_gen": [
        # Phase 1-7
        "single_shot", "react", "chain_of_thought", "test_driven", "retry_on_fail",
        # Phase 8 code-gen additions
        "multi_agent", "self_consistency", "program_aided", "tool_use_with_validation",
    ],
}

# --- streaming_react conditional registration ---
# Read the verification outcome and append to html_extract list iff PASS.
def _streaming_ok() -> bool:
    """Read 08-05-VERIFY.md to decide. Defaults to False if file is missing."""
    from pathlib import Path
    verify_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / ".planning" / "phases" / "08-expand-harness-family" / "08-05-VERIFY.md"
    )
    if not verify_path.exists():
        return False
    try:
        text = verify_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("**Outcome:**"):
                return "PASS" in line
    except OSError:
        return False
    return False


if _streaming_ok():
    HARNESSES_BY_TASK_TYPE["html_extract"].append("streaming_react")

__all__ = ["Harness", "HarnessResult", "HARNESSES", "HARNESSES_BY_TASK_TYPE"]
