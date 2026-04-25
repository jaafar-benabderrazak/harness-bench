import ast
import importlib
import inspect

from harness_eng.harnesses import HARNESSES


def test_all_harnesses_registered():
    assert set(HARNESSES.keys()) == {
        # HTML-extraction family (Phase 1-7)
        "single_shot", "react", "plan_execute", "reflexion", "minimal",
        # Code-gen family (Phase 1-7)
        "chain_of_thought", "test_driven", "retry_on_fail",
        # Phase 8 — agent-pattern family
        "tree_of_thoughts", "multi_agent", "react_with_replan",
        "self_consistency", "program_aided", "tool_use_with_validation",
        "streaming_react", "cached_react",
    }


def test_harnesses_instantiate():
    for name, cls in HARNESSES.items():
        inst = cls()
        assert inst.name == name


def test_no_harness_imports_anthropic_at_module_level():
    """Module-level imports of anthropic are forbidden. Deferred imports inside
    method bodies are allowed — model.py and streaming_react.py both use the
    deferred-import pattern (the import only runs when the method is called)."""
    for name in HARNESSES:
        mod = importlib.import_module(f"harness_eng.harnesses.{name}")
        src = inspect.getsource(mod)
        tree = ast.parse(src)
        # Only check Import / ImportFrom nodes that are direct children of the Module body
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "anthropic", \
                        f"{name} imports anthropic at module level"
            elif isinstance(node, ast.ImportFrom):
                assert node.module != "anthropic", \
                    f"{name} imports from anthropic at module level"
