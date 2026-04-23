"""The seal: only harness_eng.model may import the anthropic SDK.

Any other module that imports anthropic breaks the "held the model constant"
claim the article stands on. Enforced by AST walk, not convention — a reviewer
reading code can miss it, pytest cannot.
"""
from __future__ import annotations

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src" / "harness_eng"
ALLOWED: set[str] = {"model.py"}


def _imports_anthropic(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name == "anthropic" or n.name.startswith("anthropic."):
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module == "anthropic" or node.module.startswith("anthropic.")):
                return True
    return False


def test_only_model_py_imports_anthropic():
    violators = []
    for path in SRC_ROOT.rglob("*.py"):
        rel = path.relative_to(SRC_ROOT).as_posix()
        if rel in ALLOWED or any(part == rel for part in ALLOWED):
            continue
        # Allow only model.py; everything else must NOT import anthropic.
        if path.name == "model.py" and path.parent == SRC_ROOT:
            continue
        if _imports_anthropic(path):
            violators.append(rel)
    assert not violators, (
        "Non-model modules import anthropic — the experimental seal is broken. "
        f"Violators: {violators}"
    )
