# Deferred Items — Phase 08

## Out-of-scope failures observed during 08-04 execution

### test_model_seal.py::test_only_model_py_imports_anthropic FAILS

- **File causing failure:** `src/harness_eng/harnesses/streaming_react.py` (untracked working-tree file from Plan 08-05's territory)
- **Why deferred:** Plan 08-04 only owns `program_aided.py` + `tool_use_with_validation.py`. Both are AST-seal-clean (verified). The streaming_react.py import-of-anthropic is a Plan 08-05 concern (its CONTEXT decision #7 explicitly allows the harness to live as Anthropic-only against the streaming code path).
- **Other untracked files in tree (not Plan 08-04 scope):** `multi_agent.py`, `tree_of_thoughts.py`, `self_consistency.py` (plans 08-02, 08-03 territory). These do not break the seal.
- **Action for downstream plans:** Plan 08-05 must either (a) remove direct anthropic imports and route via model.py, or (b) update test_model_seal allowlist with rationale.

## Out-of-scope observations during 08-02 execution

- **test_model_seal failure persists** (streaming_react.py — Plan 08-05 territory). Did NOT attempt to fix. All 8 new tests added by 08-02 (3 ToT + 2 replan + 3 cached_react) pass; the three new harness files are AST-seal-clean.
- **Untracked working-tree files from prior abandoned attempts:** `multi_agent.py`, `program_aided.py`, `self_consistency.py`, `tool_use_with_validation.py`, `streaming_react.py` (some committed as `e95355a`). Plan 08-02 left them untouched. Their fates belong to Plans 08-03/04/05.
