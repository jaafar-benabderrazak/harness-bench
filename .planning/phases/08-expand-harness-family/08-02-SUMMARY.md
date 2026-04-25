---
phase: 08-expand-harness-family
plan: 02
subsystem: harnesses
tags: [tree_of_thoughts, react_with_replan, cached_react, html_extract, react-derivatives]

# Dependency graph
requires:
  - phase: 04-runner-manifests
    provides: TOOL_WHITELIST + _step_model allowlist enforcement (every harness inherits)
  - phase: 08-expand-harness-family
    provides: 08-01 foundation surface (per-call temperature override, run_python tool, jsonschema dep)
provides:
  - tree_of_thoughts harness — propose-3, deterministic-score, submit-with-winner control flow
  - react_with_replan harness — two-consecutive-NO_MATCH-on-same-selector replan trigger + replan_triggered trace event
  - cached_react harness — cell-scoped (html_hash, selector) cache as a local var in _execute (NEVER on the instance)
  - 8 new control-flow pytests (3 ToT + 2 replan + 3 cached_react)
affects: [08-06, 08-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Heuristic candidate scoring (deterministic): num_matches / mean_text_length — no second model call"
    - "Two-consecutive-NO_MATCH-on-same-selector detection via last_selector + last_was_nomatch state across loop iterations"
    - "Cell-scoped result cache as a method-local — structural guarantee against cross-cell leakage when runner reuses harness instances"
    - "Per-harness control-flow test pattern: monkeypatch model_call + monkeypatch _dispatch_tool, capture Tracer.log events"

key-files:
  created:
    - src/harness_eng/harnesses/tree_of_thoughts.py
    - src/harness_eng/harnesses/react_with_replan.py
    - src/harness_eng/harnesses/cached_react.py
    - tests/test_tree_of_thoughts.py
    - tests/test_react_with_replan.py
    - tests/test_cached_react.py
  modified:
    - .planning/phases/08-expand-harness-family/deferred-items.md

key-decisions:
  - "tree_of_thoughts scoring is HEURISTIC (deterministic num_matches/mean_text_len), NOT model-judged — per CONTEXT decision #2 to keep cost comparable to single_shot + 1 turn"
  - "react_with_replan trigger = TWO consecutive NO_MATCH on the SAME selector (not N turns of no progress) — per CONTEXT decision #3, cheapest signal that catches the most common stall pattern observed in existing react traces"
  - "cached_react cache is a LOCAL VARIABLE in _execute, never on self — structural guarantee per CONTEXT decision #8 + Pitfall 2; test_cache_is_not_a_self_attribute prevents regression"
  - "Cache hits are still counted as tool_calls in usage (the model still emitted the call) but tagged cache_hit=True in the trace so analysis can split amortized vs un-amortized calls"

patterns-established:
  - "Deterministic candidate scoring as a free function (_score_candidate) — keeps the harness method body lean and the formula independently testable"
  - "Replan trigger uses paired loop-iteration state (last_selector + last_was_nomatch) reset across non-css_select tool calls — clean, no separate state machine"
  - "Cache lookup ONLY for css_select; other tools (read_html, extract_text) bypass cache and go through normal _dispatch_tool path"

requirements-completed: [HARN-08, HARN-10, HARN-15]

# Metrics
duration: 5 min
completed: 2026-04-25
---

# Phase 08 Plan 02: HTML React-Derivatives Summary

**Three HTML-only React-derivative harnesses (`tree_of_thoughts`, `react_with_replan`, `cached_react`) implemented with their distinguishing structural twists — heuristic candidate scoring, two-NO_MATCH replan detection, cell-scoped local-variable cache — plus 8 control-flow pytests that pin each twist down structurally rather than via prompt text.**

## Performance

- **Duration:** ~5 min (~4 min 44 s wall clock)
- **Started:** 2026-04-25T19:58:40Z
- **Completed:** 2026-04-25T20:03:24Z
- **Tasks:** 3
- **Files created:** 6 (3 harnesses + 3 test files)
- **Files modified:** 1 (`deferred-items.md` — out-of-scope notes)

## Accomplishments

- `tree_of_thoughts.py` implements three-stage flow: toolless propose-3, deterministic per-candidate `css_select` + score, final submit_answer using winner's extraction text in context. Free helper `_score_candidate(matches: list[str]) -> float` returns `num_matches / max(avg_len, 1.0)` (zero for empty). Free helper `_parse_candidates(text: str) -> list[str]` parses model-output numbered/bulleted lists. `TOOL_WHITELIST = {css_select, submit_answer}`.
- `react_with_replan.py` implements standard ReAct loop body with two extra state variables (`last_selector`, `last_was_nomatch`) tracking the last css_select. On the second consecutive NO_MATCH on the SAME selector: emits `replan_triggered` trace event AND injects an extra revise-plan user message before the next model call. Non-css_select tool calls reset the state. `TOOL_WHITELIST = {read_html, css_select, extract_text, submit_answer}`.
- `cached_react.py` implements standard ReAct loop with a method-local `cache: dict[tuple[str, str], str] = {}` keyed by `(html_hash, selector)`. Cache hits emit tracer events tagged `cache_hit=True` (so analysis can split amortized vs un-amortized calls) and increment `usage.tool_calls` (the model still produced the call). Cache lookups only happen for `css_select`; other tools bypass. `TOOL_WHITELIST = {read_html, css_select, extract_text, submit_answer}`.
- 8 control-flow tests, each model-mocked end-to-end via `monkeypatch` on `base_module.model_call` + `Harness._dispatch_tool` + `Tracer.log`. The cached_react test set includes `test_cache_does_not_leak_across_cells` (re-running the same harness instance dispatches twice — proves cache is not on self) and `test_cache_is_not_a_self_attribute` (asserts `not hasattr(harness, 'cache')`).
- All 3 new harness files AST-seal-clean (no `import anthropic`, no `from anthropic`, no `self.cache` substring anywhere — including docstrings).

## Task Commits

Each task committed atomically:

1. **Task 1: tree_of_thoughts harness with heuristic candidate scoring** — `815ca89` (feat)
2. **Task 2: react_with_replan harness with two-NO_MATCH replan trigger** — `25a9165` (feat)
3. **Task 3: cached_react harness with cell-scoped local-variable cache** — `bd467ae` (feat)

**Plan metadata commit:** to follow this summary write.

## Files Created/Modified

- `src/harness_eng/harnesses/tree_of_thoughts.py` — TreeOfThoughtsHarness class, `_score_candidate`, `_parse_candidates`
- `src/harness_eng/harnesses/react_with_replan.py` — ReActWithReplanHarness class with two-NO_MATCH detection
- `src/harness_eng/harnesses/cached_react.py` — CachedReActHarness class with method-local cache
- `tests/test_tree_of_thoughts.py` — 3 tests (empty-score, specificity preference, full propose-score-submit)
- `tests/test_react_with_replan.py` — 2 tests (positive trigger same selector, negative on different selectors)
- `tests/test_cached_react.py` — 3 tests (within-cell hit, cross-cell isolation, no-self-attribute structural guarantee)
- `.planning/phases/08-expand-harness-family/deferred-items.md` — added 08-02 out-of-scope observations section

## Decisions Made

- **cached_react test_cache_hit assertion shape revised** — original plan-as-written asserted `cache_hit_events[0] is False; cache_hit_events[1] is True`. But the test monkeypatches `Harness._dispatch_tool`, which means the dispatch path's internal `tracer.log("tool_call", ...)` is replaced, so the FIRST css_select never emits a `tool_call` trace event. Only the cache-hit branch emits its own manual `tool_call` event. Test was rewritten to assert (a) `dispatched == [".a"]` (one dispatch only), (b) at least one `cache_hit=True` trace event recorded. Both assertions still pin the same control-flow truth; the rewrite only fixes a leaky test fixture, not the harness behavior.
- **Module docstring rephrasing in cached_react** — original plan-as-written docstring contained the literal string `NOT self.cache` to communicate the constraint. The plan's verification step `assert 'self.cache' not in src` rejected that substring (intentionally — the verification grep is the structural guarantee). Rephrased to "NOT an instance attribute" so the docstring conveys the same idea without tripping the seal grep.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] cached_react test_cache_hit_on_repeated_selector_within_cell assertions were inconsistent with the test's own monkeypatch fixture**

- **Found during:** Task 3 verification (`pytest tests/test_cached_react.py -q`)
- **Issue:** Test as written in plan asserted `len(cache_hit_events) >= 2` and `cache_hit_events[0] is False`. This assumed both the dispatch path and the cache-hit path emit `tool_call` trace events that the test capture would see. But the test ALSO monkeypatches `Harness._dispatch_tool` to a lambda that bypasses the real method's internal `tracer.log("tool_call", ...)`. Net: the first css_select goes through the lambda and emits no event; only the cache-hit branch (which calls `tracer.log` directly) is visible to the capture. Test failed `assert 1 >= 2`.
- **Fix:** Rewrote assertions to (a) `dispatched == [".a"]` proving only one selector reached the dispatch path, (b) `any(hit is True for hit in cache_hit_events)` proving the cache-hit branch fired. Both assertions enforce the same property the plan was after: "second call within a cell is a cache hit, not a re-dispatch." The fix is in the TEST, not the HARNESS — the harness control flow was correct from the start.
- **Files modified:** `tests/test_cached_react.py`
- **Verification:** All 3 cached_react tests pass; full new-test suite (8/8) green; harness behavior unchanged.
- **Committed in:** `bd467ae` (Task 3 commit)

**2. [Rule 1 - Bug] cached_react module docstring contained literal `self.cache` substring, tripping the AST seal grep**

- **Found during:** Task 3 verification (`assert 'self.cache' not in src`)
- **Issue:** The plan-as-written docstring read "NOT self.cache" as documentation of the prohibition. But the plan's verification command greps the source for `self.cache` as a structural seal. Documentation prose and seal-check both can't coexist when the seal greps the same string the docs cite.
- **Fix:** Rephrased docstring: "NOT an instance attribute" instead of "NOT self.cache". Same meaning; doesn't trip the seal grep.
- **Files modified:** `src/harness_eng/harnesses/cached_react.py` (docstring only)
- **Verification:** `python -c "import inspect, harness_eng.harnesses.cached_react as m; src = inspect.getsource(m); assert 'self.cache' not in src"` exits 0.
- **Committed in:** `bd467ae` (Task 3 commit; same atomic commit as Issue 1)

---

**Total deviations:** 2 auto-fixed (2 bugs). Both in cached_react Task 3; neither changed the harness control flow.
**Impact on plan:** Both fixes are mechanical inconsistencies between the plan-as-written and the plan's own verification commands. Harness behavior matches the plan's `<done>` criteria exactly. No scope creep.

## Issues Encountered

- **Pre-existing `test_model_seal.py::test_only_model_py_imports_anthropic` failure** — `src/harness_eng/harnesses/streaming_react.py` (committed in `e95355a feat(08-05)` from a previous attempt) contains a direct anthropic import, breaking the model seal. **Out of scope for Plan 08-02.** Verified the test fails before any of my work (`git stash --include-untracked` reproduced it). Logged in `.planning/phases/08-expand-harness-family/deferred-items.md` under "08-02 observations." Plan 08-05 must address.
- **Working tree had untracked harness files from prior abandoned attempts** (`multi_agent.py`, `program_aided.py`, `self_consistency.py`, `tool_use_with_validation.py`, etc.) — left untouched per scope-boundary rule. Plans 08-03/04 will own them.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

**Wave 2 HTML react-derivatives complete.** The three new harness files exist, all 8 new control-flow tests pass, AST seal is intact for the three new files. Registration in `harnesses/__init__.py` (`HARNESSES` dict + `HARNESSES_BY_TASK_TYPE`) is intentionally deferred to Plan 08-06 — these harnesses are NOT yet discoverable via `HARNESSES`, NOT yet in the matrix. That is the planned shape of Wave 2.

**Open in Phase 8:**

- Plan 08-03 (`multi_agent` + `self_consistency`): can run in parallel with Plan 08-04. Existing untracked `multi_agent.py` / `self_consistency.py` files in the working tree may or may not be a starting point — Plan 08-03 owns the choice.
- Plan 08-04 (`program_aided` + `tool_use_with_validation`): same parallel-with-08-03 status.
- Plan 08-05 (`streaming_react`): owns the existing committed `streaming_react.py` and the resulting `test_model_seal` failure.
- Plan 08-06 (registration): wires all 8 new harnesses into `HARNESSES` + `HARNESSES_BY_TASK_TYPE` + updates `tests/test_harness_registry.py` and `tests/test_tool_allowlist.py::EXPECTED`.
- Plan 08-07 (freeze-tag move): the single forward move of `harnesses-frozen` after all eight harnesses + `tools.py` + `__init__.py` registration land.

## Self-Check: PASSED

**Files checked:**

- `src/harness_eng/harnesses/tree_of_thoughts.py` — FOUND (108 lines, well above min_lines: 60)
- `src/harness_eng/harnesses/react_with_replan.py` — FOUND (90 lines, well above min_lines: 60)
- `src/harness_eng/harnesses/cached_react.py` — FOUND (96 lines, well above min_lines: 60)
- `tests/test_tree_of_thoughts.py` — FOUND (3 tests pass)
- `tests/test_react_with_replan.py` — FOUND (2 tests pass)
- `tests/test_cached_react.py` — FOUND (3 tests pass)

**Commits checked:**

- `815ca89` — FOUND (Task 1: tree_of_thoughts)
- `25a9165` — FOUND (Task 2: react_with_replan)
- `bd467ae` — FOUND (Task 3: cached_react)

**Test suite:** 8/8 new tests pass. Full suite 86/87 (1 pre-existing failure in `test_model_seal` from `streaming_react.py` outside this plan's scope, documented in deferred-items.md).

**AST seals:**

- `tree_of_thoughts.py` — no anthropic imports
- `react_with_replan.py` — no anthropic imports
- `cached_react.py` — no anthropic imports, no `self.cache` substring, no `self._cache` substring

---
*Phase: 08-expand-harness-family*
*Completed: 2026-04-25*
