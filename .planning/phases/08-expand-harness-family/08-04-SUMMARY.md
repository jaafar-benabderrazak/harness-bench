---
phase: 08-expand-harness-family
plan: 04
subsystem: harnesses
tags: [program_aided, tool_use_with_validation, jsonschema, run_python, harness]

# Dependency graph
requires:
  - phase: 08-01
    provides: run_python tool in TOOL_IMPLS + jsonschema>=4.20.0 runtime dep
provides:
  - ProgramAidedHarness — code-gen-only harness consuming run_python during reasoning (PaL-paper shape)
  - ToolUseWithValidationHarness — both task types; jsonschema-validates every non-submit tool call against tools.py TOOL_SCHEMAS; new stop_reason="schema_validation_exhausted"
affects: [08-06, 08-07, 08-08]

# Tech tracking
tech-stack:
  added: []  # all infra already added in 08-01
  patterns:
    - jsonschema validators pre-built once at module load (Draft202012Validator per tool from TOOL_SCHEMAS)
    - structured SCHEMA_VIOLATION error string surfaces violation path + required + properties
    - per-task-type tool subset selection (EXEC_TOOLS_HTML vs EXEC_TOOLS_CODE) under a UNION TOOL_WHITELIST

key-files:
  created:
    - src/harness_eng/harnesses/program_aided.py
    - src/harness_eng/harnesses/tool_use_with_validation.py
    - tests/test_program_aided.py
    - tests/test_tool_use_with_validation.py
  modified: []

key-decisions:
  - "program_aided whitelist is exactly {run_python, submit_answer} — execution-as-reasoning, distinct from test_driven's run_tests/pytest grading model"
  - "tool_use_with_validation pre-builds Draft202012Validator instances at module load — schemas are static; rebuilding per call wastes work"
  - "submit_answer NOT validated — it's the universal output channel (HARN-06); loose schema by design; the grader catches empty/malformed submissions, not the harness"
  - "MAX_VALIDATION_RETRIES=3; on the 3rd violation the cell fails with new stop_reason='schema_validation_exhausted' (analysis stop-reason chart picks this up automatically)"
  - "tool_use_with_validation TOOL_WHITELIST is the UNION of HTML + code tools (read_html, css_select, extract_text, check_syntax, run_tests, submit_answer); per-task subset selected at runtime via build_tool_list — keeps allowlist enforcement correct for both task types"
  - "validate against TOOL_SCHEMAS as-is (no per-harness override) per CONTEXT decision #6 — zero new infrastructure; if schemas drift, this harness drifts in lockstep, intentional"

patterns-established:
  - "Module-load validator pre-build: dict comprehension over TOOL_SCHEMAS at import time; deterministic, fast, no per-call rebuild"
  - "Structured-error tool_result on schema failure: surface message + path + required + properties so the model can self-correct without seeing the raw schema dict"

requirements-completed: [HARN-12, HARN-13]

# Metrics
duration: 3min30s
completed: 2026-04-25
---

# Phase 08 Plan 04: program_aided + tool_use_with_validation Harnesses Summary

**Two harnesses landed: program_aided (code-gen-only, uses run_python from 08-01 to verify intermediate values during reasoning) and tool_use_with_validation (both task types, jsonschema-validates every non-submit tool call against tools.py TOOL_SCHEMAS, fails the cell with new stop_reason='schema_validation_exhausted' after 3 violations). Both files SDK-clean, AST seal passes, 8/8 control-flow tests green, infra reused as-is from Plan 08-01.**

## Performance

- **Started:** 2026-04-25T19:58:32Z
- **Completed:** 2026-04-25T20:01:54Z
- **Duration:** ~3 min 30 sec wall-clock
- **Tasks:** 2 (one per harness)
- **Files created:** 4 (2 src + 2 tests); files modified: 0

## Accomplishments

- `program_aided.py` — `ProgramAidedHarness`, code-gen-only. `TOOL_WHITELIST = {run_python, submit_answer}`. ReAct-shape loop: model calls `run_python` to verify intermediate values, then `submit_answer` with final code. Emits `program_aided_run_python` trace event before each subprocess execution (code length only, not the body — keeps trace bounded). Rejects `html_extract` tasks cleanly (returns `(None, "no_submit")` without making a model call).
- `tool_use_with_validation.py` — `ToolUseWithValidationHarness`, both task types. `TOOL_WHITELIST` = UNION of HTML + code tools + submit_answer. Per-task subset selected at runtime via `build_tool_list(EXEC_TOOLS_HTML | EXEC_TOOLS_CODE)`. Pre-builds `Draft202012Validator` per tool at module load from `TOOL_SCHEMAS[name]['input_schema']`. Validates every non-submit tool call before dispatch; on `ValidationError` returns a structured `SCHEMA_VIOLATION` tool_result and increments `validation_failures`; after 3 violations returns `(None, "schema_validation_exhausted")`. Emits `schema_validation_pass` and `schema_validation_fail` trace events.
- 3 program_aided tests pass: run_python-before-submit ordering, html-task rejection, whitelist invariant.
- 5 tool_use_with_validation tests pass: validate-pass, validate-fail-required-missing, unknown-tool-passes-through, 3-violations-yield-exhausted, valid-flow-proceeds-to-submit.
- Plan-targeted suite: 8/8 pass.

## Task Commits

Each task committed atomically (note: see Issues Encountered re: Task 2 attribution):

1. **Task 1: program_aided harness using run_python tool** — `47307d1` (feat)
2. **Task 2: tool_use_with_validation harness with jsonschema retry loop** — files committed under `3888ac5` (parallel-agent attribution collision; see Issues Encountered). File contents are byte-identical to what was authored for this plan.

## Files Created

- `src/harness_eng/harnesses/program_aided.py` (69 lines) — `ProgramAidedHarness` class; PaL-paper-shape execution-as-reasoning
- `src/harness_eng/harnesses/tool_use_with_validation.py` (117 lines) — `ToolUseWithValidationHarness` class; module-level `_VALIDATORS` dict; `MAX_VALIDATION_RETRIES = 3`; helper `_validate_args(name, args) -> str | None`
- `tests/test_program_aided.py` (49 lines) — 3 control-flow tests
- `tests/test_tool_use_with_validation.py` (76 lines) — 5 control-flow tests

## Decisions Made

- **`submit_answer` is intentionally NOT validated.** It is the universal output channel (HARN-06). Its schema is loose by design (both `fields: object` and `code: string` keys are optional in `TOOL_SCHEMAS`), and the grader — not the harness — judges submissions. Validating it would force the model to provide both keys for both task types, which contradicts the universal-channel pattern.
- **TOOL_WHITELIST is the UNION across task types** (read_html / css_select / extract_text / check_syntax / run_tests / submit_answer). Per-task subset selection happens at runtime via `EXEC_TOOLS_HTML` / `EXEC_TOOLS_CODE` lists fed through `build_tool_list`. The allowlist enforcement in `_step_model` then checks `passed ⊆ TOOL_WHITELIST` — passes for both task types because UNION ⊇ each subset.
- **Validators pre-built at module load.** Schemas in `tools.py` are static; per-call rebuild costs nothing functional but adds noise. Dict-comprehension at import time is deterministic.
- **`SCHEMA_VIOLATION` error string surfaces enough context for the model to self-correct without the schema dict** (message, path, required, properties). The model never sees the raw schema — only the structured violation summary.
- **No retry-counter reset** between distinct tool call sites within a cell. The plan's must_haves wording mentions "same call site" but the operational interpretation per CONTEXT decision #6 is "per-cell" — once the model hits 3 cumulative violations within a single cell, the cell fails. Tracked via `validation_failures` int local to `_execute`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Widened test mock signatures from `(system, messages, tools=None, *, temperature=None)` to `(system, messages, tools=None, **_kw)`**

- **Found during:** Task 1 test authoring
- **Issue:** The plan's test snippet used the explicit `*, temperature=None` kwarg in fake_call signatures. This works today but is brittle — any future kwarg added to `model.call()` would break these mocks (precisely the mistake 08-01 already fixed in `test_tool_allowlist.py`).
- **Fix:** Used `**_kw` instead in both test files. Forward-compatible with any future `model.call()` signature additions. Pattern is established in 08-01's "patterns-established" section.
- **Files modified:** `tests/test_program_aided.py`, `tests/test_tool_use_with_validation.py`
- **Verification:** all 8 plan tests pass.
- **No new commit** — change was authored as part of Task 1 + Task 2 commits.

---

**Total deviations:** 1 (consistency-with-08-01-pattern adjustment, applied at authoring time).

## Issues Encountered

- **Parallel-agent commit attribution collision.** During Task 2 verification, my attempt to commit `tool_use_with_validation.py` + `tests/test_tool_use_with_validation.py` was preempted by a parallel Plan 08-05 agent which staged a superset including these two files and committed them under message `feat(08-05): implement streaming_react harness ...` (`3888ac5`). The committed file contents are byte-identical to what I authored for Plan 08-04 (verified via `git show 3888ac5 -- src/harness_eng/harnesses/tool_use_with_validation.py`; `git diff HEAD` returns empty for both files). The work is in main. The misattribution in commit message is documented here for record. Follow-up Plan 08-06 / 08-07 freeze-tag move can correct attribution by referencing this SUMMARY in their notes.
- **Pre-existing test_model_seal failure (out of scope).** `test_model_seal.py::test_only_model_py_imports_anthropic` FAILS due to `streaming_react.py` (Plan 08-05 territory) using deferred `from anthropic import Anthropic` inside a method body. The seal's AST walk catches this. Plan 08-05's commit (`3888ac5`) explicitly anticipates the failure and defers the fix to Plan 08-06. My harnesses (`program_aided.py`, `tool_use_with_validation.py`) are AST-seal-clean — verified by independent AST walk in this session. Logged in `.planning/phases/08-expand-harness-family/deferred-items.md`.
- **Untracked working-tree files from sibling plans.** During execution, `cached_react.py`, `multi_agent.py`, `self_consistency.py`, `tree_of_thoughts.py` and their tests appeared as untracked artifacts of parallel-agent work. None are 08-04 scope; left untouched. Most have since been committed by their respective plan agents.
- **STATE.md custom schema persists.** Per 08-01 SUMMARY's documented gsd-tools incompatibility, the state helpers (`advance-plan`, `update-progress`, `record-metric`, `record-session`) reject this STATE.md schema. Will use manual `Edit` for STATE.md (consistent with 08-01).
- **REQUIREMENTS.md has no HARN-08..15 rows yet.** Same situation as 08-01: per-plan harness rows have not been pre-added to the traceability table. Per 08-01's documented choice and noting that requirements `mark-complete` would fail on missing rows, leaving REQUIREMENTS.md untouched. The plan's `requirements: [HARN-12, HARN-13]` frontmatter is satisfied by the artifacts being merged; Plan 08-06 (registration) or 08-07 (freeze-tag move) is the right place to bulk-add the HARN-08..15 rows + check them off.

## User Setup Required

None — `run_python` already runs locally via `sys.executable`; `jsonschema` already declared as a runtime dep in `pyproject.toml` (Plan 08-01).

## Next Phase Readiness

- Plan 08-05 (`streaming_react`): unrelated to this plan's surface; proceeded in parallel and is already merged.
- Plan 08-06 (registration + tests + analysis colors): must register `program_aided` in `HARNESSES_BY_TASK_TYPE["code_gen"]`, register `tool_use_with_validation` in BOTH `HARNESSES_BY_TASK_TYPE["html_extract"]` and `["code_gen"]`, add both to `HARNESSES` registry, update `tests/test_harness_registry.py::test_all_harnesses_registered`, update `tests/test_tool_allowlist.py::EXPECTED`, add 2 entries to `analysis.py::HARNESS_COLORS`. Plan 08-06 is also the right place to add HARN-08..15 rows to REQUIREMENTS.md and check off HARN-12/13 (alongside its other harness registrations).
- Plan 08-07 (freeze-tag move): includes both new harness files + tools.py (run_python from 08-01) + model.py + base.py (temperature from 08-01) in the per-file SHA log. The new stop_reason `schema_validation_exhausted` will appear in matrix outputs from `tool_use_with_validation` cells; the analysis stop-reason chart will pick it up without code change.

## Self-Check: PASSED

**Files checked:**

- `src/harness_eng/harnesses/program_aided.py` — FOUND (69 lines, ProgramAidedHarness, whitelist={run_python, submit_answer})
- `src/harness_eng/harnesses/tool_use_with_validation.py` — FOUND (117 lines, ToolUseWithValidationHarness, MAX_VALIDATION_RETRIES=3, _VALIDATORS dict pre-built)
- `tests/test_program_aided.py` — FOUND (3 tests)
- `tests/test_tool_use_with_validation.py` — FOUND (5 tests)

**Commits checked:**

- `47307d1` — FOUND (Task 1: program_aided)
- `3888ac5` — FOUND (Task 2 files committed under streaming_react message; content byte-identical to authored Task 2; documented in Issues Encountered)

**Test suite:** 8/8 plan-targeted pass; 78/79 full-suite pass (1 pre-existing unrelated failure in test_model_seal due to Plan 08-05's streaming_react.py — out of scope, logged in deferred-items.md).

**AST seal on both new harnesses:** confirmed via `python -c "import inspect; ...; assert 'import anthropic' not in src and 'from anthropic' not in src"` — both clean.

---
*Phase: 08-expand-harness-family*
*Completed: 2026-04-25*
