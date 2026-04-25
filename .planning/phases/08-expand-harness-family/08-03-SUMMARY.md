---
phase: 08-expand-harness-family
plan: 03
subsystem: harnesses
tags: [multi_agent, self_consistency, isolated_histories, temperature, ast_normalization, voting]

# Dependency graph
requires:
  - phase: 08-expand-harness-family
    provides: per-call temperature kwarg on Harness._step_model (Plan 08-01) — required for self_consistency sample diversity
provides:
  - MultiAgentHarness — three isolated planner/executor/critic message histories with explicit Handoff TypedDict copy-between-roles (CrewAI/AutoGen-faithful)
  - SelfConsistencyHarness — N=5 samples at temperature=0.7; per-field majority for HTML, AST-normalized majority for code-gen
  - Handoff TypedDict + _render_handoff helper (multi_agent.py local; not exported)
  - _normalize_code helper (self_consistency.py local; ast.unparse round-trip with raw fallback on SyntaxError)
affects: [08-06, 08-07, 08-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Three-list isolated-history pattern for multi-role harnesses (NOT a shared message log) — sets reference for future agent-pattern harnesses
    - ast.unparse(ast.parse(code)) for whitespace+comment-insensitive code voting; raw-string fallback on SyntaxError
    - Per-call temperature kwarg consumption pattern via Wave-1 _step_model — reusable surface for any future stochastic harness

key-files:
  created:
    - src/harness_eng/harnesses/multi_agent.py
    - src/harness_eng/harnesses/self_consistency.py
    - tests/test_multi_agent.py
    - tests/test_self_consistency.py
  modified: []

key-decisions:
  - "multi_agent uses three SEPARATE messages lists (planner / executor / critic), never a shared log — faithful to CrewAI/AutoGen and per CONTEXT decision #1"
  - "multi_agent TOOL_WHITELIST is the UNION of HTML + code-gen executor needs (read_html, css_select, extract_text, check_syntax, run_tests, submit_answer); per-task-type subset is chosen at runtime via build_tool_list, and _step_model's allowlist subset check still passes"
  - "self_consistency HTML voting is per-field majority (CONTEXT decision #4) — one wrong field on one sample doesn't tank the whole record"
  - "self_consistency code-gen voting normalizes via ast.unparse before counting; the WINNING raw sample is returned (not the normalized form) so the model's actual submission is what gets graded"
  - "_normalize_code falls back to raw on SyntaxError so a single broken sample doesn't crash the vote"
  - "multi_agent does ONE bounded retry on critic-CRITIQUE feedback to cap token cost at ~3x single-log; documented in article weaknesses"

patterns-established:
  - "Forward-compat mock signatures (use **_kw on test fakes) — already a Plan 08-01 pattern; reused in all multi_agent tests"
  - "AST normalization for code voting/comparison: ast.unparse(ast.parse(s)) with raw-string fallback on SyntaxError"
  - "Isolated-histories pattern for multi-role harnesses: each role owns its own list[dict[str, Any]]; structured handoff dicts are explicitly stringified and copied via _render_handoff before being prepended to the next role's first user message"

requirements-completed:
  - HARN-09  # multi_agent
  - HARN-11  # self_consistency

# Metrics
duration: 3min
completed: 2026-04-25
---

# Phase 08 Plan 03: Cross-Task Harnesses Summary

**multi_agent (three isolated planner/executor/critic histories with explicit Handoff copies) + self_consistency (N=5 samples at temperature=0.7; per-field majority for HTML, AST-normalized majority for code-gen) — both consume the Wave-1 temperature kwarg, both ship with control-flow tests asserting the documented semantics.**

## Performance

- **Duration:** ~3 min (201 seconds wall clock)
- **Started:** 2026-04-25T19:58:21Z
- **Completed:** 2026-04-25T20:01:42Z
- **Tasks:** 2
- **Files created:** 4 (2 source + 2 tests; 566 total lines)

## Accomplishments

- `multi_agent.py` (168 lines) implements the three-role pattern with three isolated `messages` lists. PLANNER (no tools) -> EXECUTOR (per-task-type tools, ReAct-shape loop, ONE bounded retry on critique) -> CRITIC (no tools). The `Handoff` TypedDict + `_render_handoff` helper formalize the explicit string-copy contract between roles.
- `self_consistency.py` (147 lines) wraps the single_shot pattern. Calls `_step_model(..., temperature=SAMPLE_TEMPERATURE)` exactly N_SAMPLES=5 times. HTML branch votes per-field; code branch votes over `ast.unparse`-normalized code and returns the raw winning sample.
- 8 control-flow tests pass (3 multi_agent + 5 self_consistency, including a bonus AST-normalized-vote test beyond the planned 4).
- AST seal clean for both new files (no anthropic imports); both importable; both inherit allowlist enforcement from Plan 08-01's `_step_model`.

## Task Commits

Each task committed atomically:

1. **Task 1: Implement multi_agent harness with isolated planner/executor/critic histories** — `f74b886` (feat)
2. **Task 2: Implement self_consistency with N=5 samples at temperature=0.7** — `920cebc` (feat)

**Plan metadata commit:** to follow this summary write.

## Files Created/Modified

- `src/harness_eng/harnesses/multi_agent.py` — `MultiAgentHarness` + `Handoff` TypedDict + `_render_handoff` + `PLANNER_SYSTEM` / `EXECUTOR_SYSTEM_HTML` / `EXECUTOR_SYSTEM_CODE` / `CRITIC_SYSTEM` constants
- `src/harness_eng/harnesses/self_consistency.py` — `SelfConsistencyHarness` + `N_SAMPLES=5` / `SAMPLE_TEMPERATURE=0.7` constants + `_normalize_code` helper
- `tests/test_multi_agent.py` — 3 tests: distinct-systems, planner-first, isolated-histories
- `tests/test_self_consistency.py` — 5 tests: normalize-strips-comments, normalize-fallback-on-syntax-error, exactly-5-calls-at-0.7, per-field-majority-independent, code-uses-ast-normalized-majority

## Decisions Made

- **TOOL_WHITELIST as UNION rather than per-task-type whitelist:** `multi_agent` declares `TOOL_WHITELIST` = the union across HTML + code-gen executor needs. Per-task-type subset is enforced internally by selecting a different `EXECUTOR_TOOLS_*` list at runtime; `_step_model`'s subset check (Plan 08-01 allowlist surface) still passes because the runtime subset is a subset of the declared union. Alternative was per-task-type whitelist subclasses — rejected as it would double the file count and complicate freeze-tag bookkeeping.
- **Single bounded retry on critic feedback:** `multi_agent` retries the executor once with the critic's critique appended to a copy of the executor messages. Caps cost growth at ~3-4x single-log harnesses (matches the "documented as weakness" note in CONTEXT). No infinite critique loop.
- **Return raw winning code, not normalized:** `self_consistency._execute_code` votes on `ast.unparse`-normalized code but returns the FIRST RAW sample whose normalized form matches the winner. Rationale: the grader sees what the model actually wrote, not a re-stringified AST round-trip (which could subtly differ in formatting that downstream tools care about).
- **Bonus 5th test for AST-normalized voting:** the plan listed 4 self_consistency tests; I added a 5th explicitly verifying the code-gen branch's AST-normalized majority (3 whitespace-different but semantically-equal samples beat 2 wrong-body samples). Required to satisfy the success criterion "self_consistency code test asserts AST-normalization before voting" — a test of `_normalize_code` alone wouldn't prove the harness USES it for voting.

## Deviations from Plan

None — plan executed exactly as written. Both task code blocks copied verbatim from PLAN.md (modulo cosmetic line-length wrapping for readability and a couple of mock-signature widenings to `**_kw` for forward-compat consistency with the Plan 08-01 pattern).

The bonus 5th self_consistency test (`test_self_consistency_code_uses_ast_normalized_majority`) is not a deviation — it is required by the plan's `must_haves.truths` ("self_consistency HTML voting is per-field majority; code voting is majority over AST-normalized code string") and by the user-supplied success criterion in the execution prompt ("self_consistency code test asserts AST-normalization before voting"). The plan's task block specified 4 tests; the 5th closes the gap between those 4 and the success criterion.

## Issues Encountered

- **Pre-existing AST-seal failure in `streaming_react.py` (Plan 08-05 territory).** Full pytest run shows `tests/test_model_seal.py::test_only_model_py_imports_anthropic` FAIL because `harnesses/streaming_react.py` imports anthropic directly. This file is OUT OF SCOPE for Plan 08-03 — it was authored by Plan 08-05 and the failure was already documented in `.planning/phases/08-expand-harness-family/deferred-items.md` by Plan 08-04. Per the executor scope-boundary rule, no fix attempted. My two new harness files BOTH pass the AST seal individually (verified inline). The 8 tests I authored all pass (`pytest tests/test_multi_agent.py tests/test_self_consistency.py -v` -> 8 passed in 0.21s).
- **Other untracked Phase-8 work in working tree at start of execution:** `tree_of_thoughts.py`, `react_with_replan.py`, `cached_react.py`, `streaming_react.py`, `program_aided.py` (and matching tests) appeared as untracked when I started. They are commits from Plans 08-02, 08-04, 08-05 (`815ca89`, `25a9165`, `47307d1`, `3888ac5`) that landed before mine. Did not touch them. My commits include only Plan 08-03 files.

## User Setup Required

None — no external service configuration required. Both new harnesses are pure-Python and inherit the existing model/tool routing.

## Next Phase Readiness

**Wave-2 (cross-task harnesses) ready for downstream consumption:**

- **Plan 08-06 (Registration):** can now register `multi_agent` and `self_consistency` in `HARNESSES_BY_TASK_TYPE`. Both list `task_type = ["html_extract", "code_gen"]` (cross-task by design).
- **Plan 08-07 (Freeze-tag move):** these two new files are gated additions that must move with the freeze tag.
- **Plan 08-08 (Article refresh):** harness descriptions can be drafted now from the docstrings:
  - `multi_agent` -> CrewAI/AutoGen mapping; weakness: ~3x token cost from isolated histories
  - `self_consistency` -> Wang et al. 2022 mapping; per-field-vs-whole-string voting asymmetry across task types

**Critical reminder for downstream plans:** the multi_agent UNION whitelist means `_step_model`'s allowlist check is satisfied at any per-task-type call. Future regressions that try to NARROW the union without updating `EXECUTOR_TOOLS_*` will trigger `ToolAllowlistViolation` — that's the intended safety net.

**Open thread for Plan 08-05:** `streaming_react.py`'s direct anthropic import will still fail `test_model_seal.py` until Plan 08-05 either routes through model.py or updates the seal allowlist. Documented in `deferred-items.md`; not blocking 08-03.

## Self-Check: PASSED

**Files checked:**

- `src/harness_eng/harnesses/multi_agent.py` — FOUND (168 lines, contains `class MultiAgentHarness`)
- `src/harness_eng/harnesses/self_consistency.py` — FOUND (147 lines, contains `class SelfConsistencyHarness`)
- `tests/test_multi_agent.py` — FOUND (3 tests, contains `PLANNER`)
- `tests/test_self_consistency.py` — FOUND (5 tests, contains `temperature`)

**Commits checked:**

- `f74b886` — FOUND (Task 1)
- `920cebc` — FOUND (Task 2)

**Test results:** `pytest tests/test_multi_agent.py tests/test_self_consistency.py` -> 8/8 pass.
**AST seal (multi_agent.py + self_consistency.py only):** clean — no anthropic imports.

---
*Phase: 08-expand-harness-family*
*Completed: 2026-04-25*
