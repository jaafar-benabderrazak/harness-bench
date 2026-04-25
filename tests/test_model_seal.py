"""The seal: only harness_eng.model may import the anthropic SDK.

Any other module that imports anthropic at MODULE LEVEL breaks the "held the
model constant" claim the article stands on. Enforced by AST walk that scopes
imports — module-level only — so deferred imports inside method bodies (e.g.
`from anthropic import Anthropic` inside `streaming_react._stream_anthropic`)
are tolerated. The deferred pattern is fine because the import only runs when
the method is called by a harness that legitimately needs Anthropic-specific
streaming semantics; the module imports cleanly without anthropic installed.
"""
from __future__ import annotations

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src" / "harness_eng"
ALLOWED: set[str] = {"model.py"}


def _imports_anthropic_at_module_level(path: Path) -> bool:
    """True iff this file has a top-level (module-scope) import of anthropic.

    Imports inside class bodies, function bodies, or any nested scope are
    intentionally NOT flagged — those execute only when the caller runs them,
    so a never-called method's `import anthropic` doesn't violate the seal.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    # tree.body is the list of module-level statements ONLY. Walking it
    # directly (not ast.walk) ensures we never descend into FunctionDef /
    # ClassDef / AsyncFunctionDef / If / Try bodies.
    for node in tree.body:
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
        # Allow only model.py; everything else must NOT import anthropic at module level.
        if path.name == "model.py" and path.parent == SRC_ROOT:
            continue
        if _imports_anthropic_at_module_level(path):
            violators.append(rel)
    assert not violators, (
        "Non-model modules import anthropic at module level — the experimental "
        f"seal is broken. Violators: {violators}"
    )
