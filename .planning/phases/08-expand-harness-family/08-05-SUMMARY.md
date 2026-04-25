---
phase: 08-expand-harness-family
plan: 05
subsystem: harnesses
tags: [streaming, ollama, anthropic, react, verification]

# Dependency graph
requires:
  - phase: 08-01
    provides: run_python tool, jsonschema runtime dep, per-call temperature override
provides:
  - StreamingReActHarness with both Anthropic and Ollama streaming paths
  - Mid-stream submit_answer detection that breaks the model stream early
  - One-shot Ollama compatibility verification script + outcome document
  - Concrete verification result feeding into plan 08-06 registration policy
affects: [08-06, 08-07, article-update]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Deferred SDK imports inside method bodies (anthropic / ollama not at module scope) — required for AST seal compliance"
    - "Streaming early-termination on tool_use detection — Anthropic via content_block_start event sniffing, Ollama via per-chunk message.tool_calls aggregation"
    - "Verification scripts write a structured outcome file (08-05-VERIFY.md) consumed by downstream registration plans"

key-files:
  created:
    - "src/harness_eng/harnesses/streaming_react.py"
    - "tests/test_streaming_react.py"
    - "scripts/verify_streaming_ollama.py"
    - ".planning/phases/08-expand-harness-family/08-05-VERIFY.md"
  modified: []

key-decisions:
  - "streaming_react registered with task_type=[] in plan 08-06 (excluded from local-model matrix) — Ollama probe FAILED"
  - "Failure mode was OOM (glm-4.7-flash requires 23.4 GiB, host has 6.9 GiB) — not the predicted Ollama issue #13840 post-tool-call halt; outcome (no local matrix slot) is identical"
  - "Harness file lives in tree regardless — article cites it as 'implemented but unmatrixed', and a future Anthropic-backend run can activate it"
  - "AST seal in tests/test_harness_registry.py needs a fix in plan 08-06 to allow the deferred 'from anthropic import Anthropic' inside a method body"

patterns-established:
  - "Streaming + early-break: detect submit_answer at the earliest reachable event and exit the iterator without draining"
  - "Verification-as-input: a probe writes an outcome doc that the next plan reads to decide registration shape"

requirements-completed: [HARN-14]

# Metrics
duration: 13 min
completed: 2026-04-25
---

# Phase 8 Plan 5: streaming_react + Ollama Verify Summary

**StreamingReActHarness with Anthropic content_block_start + Ollama chunk-level submit_answer detection; Ollama probe FAILED (OOM, not the predicted post-tool-call halt) — registered in tree, excluded from local matrix.**

## Performance

- **Duration:** ~13 min total (across two executor sessions)
- **Started (this session):** 2026-04-25T20:12:32Z
- **Completed:** 2026-04-25T20:12:44Z
- **Tasks:** 3 (2 from prior session + 1 here)
- **Files created:** 4

## Accomplishments

- StreamingReActHarness implemented with both backends (Anthropic + Ollama), deferred SDK imports keeping the AST seal-compatible at module scope
- Mid-stream early-break on submit_answer: Anthropic via content_block_start event sniff, Ollama via per-chunk message.tool_calls aggregation
- 4 control-flow tests (mocked stream): submit_answer termination, whitelist invariant, no module-level anthropic import, plus an additional sanity test
- Verification script `scripts/verify_streaming_ollama.py` runs end-to-end with a 90s wall-clock guard and writes structured outcome to `08-05-VERIFY.md`
- Probe outcome: **FAIL** — registration policy for plan 08-06 is now deterministic (`task_type=[]`)

## Task Commits

1. **Task 1: streaming_react harness + control-flow tests** — `e95355a` (feat) [also touched in `3888ac5`]
2. **Task 2: Ollama compat verification script** — `fc6ff66` (feat)
3. **Task 3: Run probe + record outcome** — `19824ad` (verify)

_Plan metadata commit follows this SUMMARY._

## Files Created/Modified

- `src/harness_eng/harnesses/streaming_react.py` — StreamingReActHarness with `_stream_anthropic` (content_block_start sniff) and `_stream_ollama` (chunk loop with early break); deferred imports inside method bodies
- `tests/test_streaming_react.py` — 4 control-flow tests (mocked stream); all pass
- `scripts/verify_streaming_ollama.py` — One-shot probe with 90s wall-clock guard; writes structured outcome
- `.planning/phases/08-expand-harness-family/08-05-VERIFY.md` — `Outcome: FAIL`, elapsed 4.5s, OOM detail; implication for 08-06

## Decisions Made

- **Probe outcome FAIL → register with `task_type=[]`.** Plan 08-06 will keep `streaming_react` in `HARNESSES` dict (so it's importable / discoverable) but absent from any `HARNESSES_BY_TASK_TYPE` list. Local-model matrix will not invoke it.
- **Failure mode is OOM, not the predicted #13840 halt.** The host machine has 6.9 GiB free; glm-4.7-flash needs 23.4 GiB. The outcome (no local matrix slot) matches the predicted outcome, but the cause is different. The reference link in `08-05-VERIFY.md` (issue #13840) is now misleading and should be revisited in plan 08-07 when HARNESSES_FROZEN.md documents the exclusion.
- **Harness file stays in tree regardless.** Per CONTEXT decision #7. A future Anthropic-backend run can activate it without further code changes.
- **AST seal fix is plan 08-06's job.** The full-file string-grep in `tests/test_harness_registry.py::test_no_harness_imports_anthropic_directly` finds the deferred `from anthropic import Anthropic` inside `_stream_anthropic` and fails. Plan 06 must relax the seal to allow imports inside method bodies (or whitelist streaming_react). Per project instructions, this plan does NOT modify the seal test.

## Deviations from Plan

None — plan executed exactly as written.

The probe's failure mode (OOM rather than #13840 halt) is a finding, not a deviation: the plan explicitly anticipated FAIL as a valid outcome and routed all FAIL paths to the same registration policy.

**Total deviations:** 0
**Impact on plan:** None — verification result feeds directly into 08-06 as designed.

## Issues Encountered

- **OOM on the host machine.** glm-4.7-flash declares a 23.4 GiB working-set requirement; the host has 6.9 GiB available. Ollama returns HTTP 500 with `model requires more system memory` before any tokens stream. This means the probe could not actually exercise the streaming/tool-call path on this machine — the FAIL is environmental, not protocol-level. A larger box might still hit the predicted #13840 halt, or might pass entirely. The recorded FAIL is correct for the host the matrix will run on, which is what matters for registration.

## Deferred Issues

- AST seal fix in `tests/test_harness_registry.py::test_no_harness_imports_anthropic_directly` — plan 08-06's responsibility (intentionally untouched here).
- The `08-05-VERIFY.md` reference link to Ollama issue #13840 is now misleading (the actual failure mode was OOM); plan 08-07 should clarify this when documenting the exclusion in HARNESSES_FROZEN.md.
- A future Anthropic-backend run can activate streaming_react in the matrix; no code changes required.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Plan 08-06 (registration) has its deterministic input: `streaming_react` → `task_type=[]`. It can proceed.
- Plan 08-07 (freeze-tag move) must wait for 08-06 to land first (AST seal fix + registration).
- Article update (plan 08-08) cites streaming_react as "implemented but unmatrixed" — the file exists, the verification ran, the outcome is documented.

---
*Phase: 08-expand-harness-family*
*Completed: 2026-04-25*

## Self-Check: PASSED

- `src/harness_eng/harnesses/streaming_react.py` — FOUND
- `tests/test_streaming_react.py` — FOUND (4 tests passing)
- `scripts/verify_streaming_ollama.py` — FOUND (parses, runs)
- `.planning/phases/08-expand-harness-family/08-05-VERIFY.md` — FOUND (Outcome: FAIL)
- Commit `e95355a` — FOUND (Task 1)
- Commit `fc6ff66` — FOUND (Task 2)
- Commit `19824ad` — FOUND (Task 3 verify outcome)
