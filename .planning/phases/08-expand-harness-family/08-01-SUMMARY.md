---
phase: 08-expand-harness-family
plan: 01
subsystem: infra
tags: [tools, model, jsonschema, temperature, foundation]

# Dependency graph
requires:
  - phase: 04-runner-manifests
    provides: TOOL_WHITELIST + _step_model allowlist enforcement (the surface this plan extends)
provides:
  - run_python tool (subprocess.run, 5s timeout) registered in TOOL_IMPLS + TOOL_SCHEMAS
  - jsonschema>=4.20.0 declared as runtime dependency
  - per-call temperature override on model.call() (Anthropic + Ollama paths)
  - per-call temperature override on Harness._step_model with trace event recording
affects: [08-02, 08-03, 08-04, 08-05, 08-06, 08-07]

# Tech tracking
tech-stack:
  added: [jsonschema>=4.20.0]
  patterns:
    - run_python sibling to run_tests (no shared helper extraction — keeps freeze diff tight)
    - keyword-only temperature kwarg threaded call → backend → trace event

key-files:
  created: []
  modified:
    - pyproject.toml
    - src/harness_eng/tools.py
    - src/harness_eng/model.py
    - src/harness_eng/harnesses/base.py
    - tests/test_tools.py
    - tests/test_model_usage.py
    - tests/test_tool_allowlist.py

key-decisions:
  - "run_python kept as sibling of run_tests (no _run_python_subprocess helper extracted) per RESEARCH finding #6 — minimizes freeze-diff scope"
  - "temperature threaded as keyword-only param (Option A from RESEARCH finding #5) — backward-compatible default, end-to-end auditable via model_call trace event"
  - "model_call trace event gains temperature field so traces can prove sample diversity for self_consistency"

patterns-established:
  - "Forward-compatible mock signatures (use **_kw on test fakes that wrap model_call) — protects against future call-site additions"
  - "Per-call temperature override pattern — eff_temp = CONFIG.model.temperature if temperature is None else temperature"

requirements-completed: []  # Plan 08-01 is foundation-only — HARN-11/12/13 are *unblocked-by* this plan but *delivered-by* their harness plans (08-03 HARN-11, 08-04 HARN-12 + HARN-13). REQUIREMENTS.md will be checked off then.

# Metrics
duration: 3min
completed: 2026-04-25
---

# Phase 08 Plan 01: Foundation Summary

**run_python tool + jsonschema runtime dep + per-call temperature override (model.call + _step_model) — the four foundation surfaces every Phase 8 harness depends on, all in gated files so they land in the same freeze-tag move.**

## Performance

- **Duration:** ~3 min (192 seconds wall clock, including reinstall + full pytest)
- **Started:** 2026-04-25T19:50:07Z
- **Completed:** 2026-04-25T19:53:19Z
- **Tasks:** 3
- **Files modified:** 7 (4 source + 3 tests)

## Accomplishments

- `pyproject.toml` declares `jsonschema>=4.20.0` as runtime dep (enables `tool_use_with_validation` in Plan 08-04 without onboarding friction).
- `tools.py` exposes `run_python` tool: 5-second `subprocess.run` timeout, dispatchable via `dispatch("run_python", ctx, code=...)`, registered in both `TOOL_IMPLS` and `TOOL_SCHEMAS`. Mirrors `_tool_run_tests` security model.
- `model.call(...)` now accepts keyword-only `temperature: float | None = None`; threads through `_call_anthropic` and `_call_ollama` as required `*, temperature: float`. Default behavior preserved when kwarg omitted (falls back to `CONFIG.model.temperature`).
- `Harness._step_model(...)` accepts the same kwarg, forwards to `model_call`, and records `temperature` in the `model_call` trace event for end-to-end auditability.
- Full test suite green (59/59), with 4 new tests (2 for `run_python` + 2 for temperature override).

## Task Commits

Each task committed atomically:

1. **Task 1: Add jsonschema dep + run_python tool to tools.py** — `26e8021` (feat)
2. **Task 2: Add temperature kwarg to model.call() (Anthropic + Ollama paths)** — `46d499e` (feat)
3. **Task 3: Thread temperature through _step_model in base.py** — `d45a6ac` (feat)

**Plan metadata commit:** to follow this summary write.

## Files Created/Modified

- `pyproject.toml` — added `jsonschema>=4.20.0` to `[project] dependencies`
- `src/harness_eng/tools.py` — added `_tool_run_python` (5s subprocess timeout); registered in `TOOL_IMPLS` and `TOOL_SCHEMAS`
- `src/harness_eng/model.py` — `call()` gains keyword-only `temperature` param; `_call_anthropic` and `_call_ollama` now require `*, temperature: float` and pull from kwarg instead of `CONFIG`
- `src/harness_eng/harnesses/base.py` — `_step_model` gains keyword-only `temperature` param; forwards to `model_call`; logs `temperature` in `model_call` trace event
- `tests/test_tools.py` — 2 new tests: `test_run_python_returns_stdout`, `test_run_python_timeout_killable`
- `tests/test_model_usage.py` — 2 new tests: `test_call_uses_config_temperature_by_default`, `test_call_temperature_kwarg_overrides_config`
- `tests/test_tool_allowlist.py` — fake_call mock signature widened to `**_kw` (forward-compatible with new model.call signature)

## Decisions Made

- **Mock signature hardening (test_tool_allowlist):** rather than thread `temperature` into the existing test's local `fake_call`, widened it to `**_kw`. Pattern: every model_call mock should accept `**_kw` so future signature additions don't ripple through tests. Documented under "patterns-established."
- **No `_run_python_subprocess` helper extraction:** stuck with planner recommendation per RESEARCH finding #6. `_tool_run_python` and `_tool_run_tests` remain siblings; both are ~20 lines; extraction would muddy the freeze diff.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated `fake_call` mock in test_tool_allowlist.py to accept `**_kw`**

- **Found during:** Task 3 verification (`pytest tests/test_tool_allowlist.py`)
- **Issue:** `test_step_model_accepts_subset_of_whitelist` defined `fake_call(system, messages, tools)` with no kwargs slot. New `_step_model` calls `model_call(system, messages, tools, temperature=temperature)`, breaking the mock with `TypeError: fake_call() got an unexpected keyword argument 'temperature'`.
- **Fix:** Widened mock to `def fake_call(system, messages, tools, **_kw):`. Forward-compatible against any future kwargs added to `model.call()`.
- **Files modified:** `tests/test_tool_allowlist.py`
- **Verification:** `pytest tests/test_tool_allowlist.py -q` → 4/4 pass; full suite 59/59 pass.
- **Committed in:** `d45a6ac` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking — caused directly by current task's signature change).
**Impact on plan:** Mechanical cascade fix; no scope creep. The mock widening is a pattern future plans should follow.

## Issues Encountered

- **STATE.md test count was stale.** Plan estimated 41 + 4 = 45 tests; actual collection is 59 (test files added in Phases 5-7 not reflected in STATE.md). All pre-existing tests still green; 4 new tests added by this plan all pass. No action required beyond noting the discrepancy.
- **No new pyproject.toml lockfile to commit** — repo uses `pyproject.toml` only (no `uv.lock`/`requirements.txt`). `pip install -e .` re-resolved deps cleanly; jsonschema 4.25.1 already present in env.
- **REQUIREMENTS.md has no HARN-08..15 rows yet.** The plan's `requirements:` frontmatter lists HARN-11/12/13 because foundation work *unblocks* them. Each requirement is actually delivered by its harness plan (HARN-11 in Plan 08-03, HARN-12 + HARN-13 in Plan 08-04). Adding the rows + checking them off here would misattribute delivery. Left REQUIREMENTS.md untouched; harness plans will register and check off in sequence.
- **gsd-tools state helpers schema-mismatched.** `state advance-plan`, `update-progress`, `record-metric`, `record-session` rejected this STATE.md schema (Project State / Current Position layout predates the gsd-tools assumed schema). Fell back to manual `Edit` of the existing sections — preserves original style. Only `state add-decision` worked cleanly. Documented for future plan executors in this phase.

## User Setup Required

None — no external service configuration required. The new `run_python` tool runs locally via `sys.executable`; `jsonschema` is a pure-Python dep auto-installed via `pip install -e .`.

## Next Phase Readiness

**Foundation surface ready for Wave 2:**

- Plan 08-02 (HTML react-derivatives — `tree_of_thoughts`, `react_with_replan`, `cached_react`): no new infra needed; uses existing tools.
- Plan 08-03 (`multi_agent` + `self_consistency`): `self_consistency` can now call `_step_model(..., temperature=0.7)` for N=5 sample diversity.
- Plan 08-04 (`program_aided` + `tool_use_with_validation`): `program_aided` consumes `run_python`; `tool_use_with_validation` consumes `jsonschema`.
- Plan 08-05 (`streaming_react`): no foundation deps; will likely add streaming code path on `model.py` if needed.

**Important:** the four files modified in this plan (`pyproject.toml`, `tools.py`, `model.py`, `base.py`) are gated freeze paths. The freeze-tag move stays at the current `harnesses-frozen` SHA — it MUST move forward in Plan 08-07 only, after all Wave 2/3 harnesses land. Until then, the runner pre-flight diff check will flag these files as "modified vs freeze tag" — that is expected and intentional for the duration of Phase 8.

## Self-Check: PASSED

**Files checked:**

- `pyproject.toml` — FOUND (jsonschema declared)
- `src/harness_eng/tools.py` — FOUND (`run_python` in TOOL_IMPLS + TOOL_SCHEMAS)
- `src/harness_eng/model.py` — FOUND (`temperature` in call signature)
- `src/harness_eng/harnesses/base.py` — FOUND (`temperature` in _step_model signature)
- `tests/test_tools.py` — FOUND (8 tests, including 2 new)
- `tests/test_model_usage.py` — FOUND (4 tests, including 2 new)

**Commits checked:**

- `26e8021` — FOUND (Task 1)
- `46d499e` — FOUND (Task 2)
- `d45a6ac` — FOUND (Task 3)

**Test suite:** 59/59 pass.

---
*Phase: 08-expand-harness-family*
*Completed: 2026-04-25*
