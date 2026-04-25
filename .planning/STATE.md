# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-23)

**Core value:** Produce concrete, reproducible evidence — numbers and annotated failure traces — that harness design dominates model choice within a tier on the same frozen model.
**Current focus:** Phase 8 — Expand Harness Family (Wave 1 done; Wave 2 next)

## Current Position

Phase: 8 of 8 (Expand Harness Family + Refresh Article)
Plans complete: Phase 8 — 2 of 8 (08-01 foundation + 08-03 cross-task harnesses done); Phases 1-4, 7 delivered; Phase 5 deferred to user; Phase 6 blocked on Phase 5
Status: Phase 8 Wave 1 (foundation) + part of Wave 2 (multi_agent + self_consistency) shippable; remaining Wave 2 + Wave 3 + registration to plan

Progress: [█████████░] 88% (Phase 8 underway, 2 of 8 plans complete)

## Completed Phases

| Phase | Commits | Deliverables | Requirements closed |
|-------|---------|--------------|---------------------|
| 1. Audit and Harden Scaffold | `65ed6bd` | trace.py schema_version + fsync; grader.py NFC + casefold; model.py max_retries=0 + usage_raw; HELD_OUT.md (Option A: no hold-out); AUDIT.md | 34 (INTG-01..03, HARN-01..06, BENCH-01..04, TRACE-01..05, RUN-01/03/05/06, ANAL-01/03/04, ART-01..02, VIEW-01..04, TEST-01..02, ONB-03) |
| 2. Methodology Freeze | `389c31b` `b2965cd` `3bd1556` | Pre-registered hypothesis in README; runner `check_freeze_gate()`; HARNESSES_FROZEN.md; git tag `harnesses-frozen` | 4 (INTG-04, INTG-05, INTG-06, ONB-02) |
| 3. Multi-seed + Statistics | `9cd910a` | `wilson_ci()`; --seeds default 3; ci_low/ci_high/cost_per_success_usd columns; frontier chart error bars | 3 (RUN-02, ANAL-02, ANAL-05) |
| 4. Manifests + Tool Allowlist | `bca26d4` `4eacafb` | `TOOL_WHITELIST` on every harness; `_step_model` enforces subset check; `runs_expected.jsonl` + `runs_completed.jsonl`; --resume support; tag moved to post-allowlist HEAD | 2 (HARN-07, RUN-04) |
| 7. CI + Onboarding Polish | `54f6285` | CI matrix ubuntu + windows; `.gitattributes` pinning html/jsonl binary; README Quickstart mirrors CI sequence | 3 (BENCH-05, TEST-03, ONB-01) |

## Deferred / Blocked

| Phase | Status | Note |
|-------|--------|------|
| 5. Matrix Execution | deferred to user | Requires real ANTHROPIC_API_KEY + ~$12–25 spend. Runner is ready; `scripts/run_full.py` gated by cost estimator + freeze check. |
| 6. Article Polish | blocked on Phase 5 | Auto-drafter produces a template with numbers interpolated from summary.csv; "What surprised me" and "Implications" sections need real traces to write from. |

## Tag moves log

1. `0a44719` → `4eacafb` (Phase 4: added TOOL_WHITELIST to gated files)
2. `4eacafb` → `d0fc1f1` (CI fix: dropped unused `field` import from base.py)

Neither move invalidated any matrix runs — no matrix has been executed yet.

## Test suite state

`pytest tests/test_multi_agent.py tests/test_self_consistency.py` → 8/8 pass as of `920cebc` (Plan 08-03 merged).

- Plan 08-03 added: test_multi_agent (3 control-flow tests), test_self_consistency (5 tests including AST-normalized voting).
- Plan 08-01 added: test_tools (+2 run_python tests → 8 total), test_model_usage (+2 temperature tests → 4 total). test_tool_allowlist fake_call mock widened to **_kw for forward-compat.
- Pre-Phase-8 baseline: 41 tests as of `d0fc1f1`. The +14 above 45 (41 + 4 expected) come from test files added in interim work (test_trace_summary etc.) not previously listed in STATE.md.
- Pre-existing AST-seal failure (test_model_seal) on `harnesses/streaming_react.py` is documented in `.planning/phases/08-expand-harness-family/deferred-items.md` — not introduced by Plan 08-03; my new files (multi_agent.py + self_consistency.py) both pass the seal individually.

CI green on ubuntu-latest + windows-latest (run 24829222393).

## Repo state

- GitHub: <https://github.com/jaafar-benabderrazak/harness-bench>
- main: `d0fc1f1`
- tag `harnesses-frozen`: `d0fc1f1`
- Offline demo available: `python scripts/demo_matrix.py` — exercises pipeline with deterministic fake model

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

- No held-out fixtures (HELD_OUT.md): Option A — all 5 fixtures used in dev + matrix. Value of held-out split is marginal at 5-fixture scale; article's "honest scope" section states this plainly.
- Single frozen model (Claude Sonnet 4.6): multi-provider comparison is a separate project.
- Universal `submit_answer` tool for all harnesses: eliminates free-form-text parsing as a confound (Pitfall 12).
- [Phase 08]: Plan 08-01: foundation surface (run_python tool + jsonschema runtime dep + per-call temperature override on model.call and _step_model) landed in gated files; freeze-tag move deferred to Plan 08-07
- [Phase 08]: Plan 08-03: multi_agent (3 isolated histories, Handoff TypedDict, UNION whitelist, single bounded retry) + self_consistency (N=5 @ T=0.7, per-field majority HTML, AST-normalized majority code returning raw winning sample) — both harnesses + 8 tests landed; HARN-09 + HARN-11 satisfied

### Blockers/Concerns

- Phase 5 is user-action: requires API key + spend. Cost estimator gates the run; user must confirm.
- Phase 6 depends on real Phase 5 traces to write the "what surprised me" narrative honestly. The auto-drafter leaves that section as a stub (by design — generating fake narrative would be worse than leaving it empty).

## Session Continuity

Last session: 2026-04-25
Stopped at: Completed 08-03-PLAN.md. multi_agent + self_consistency merged in two atomic commits (`f74b886`, `920cebc`). 8/8 control-flow tests pass. Both files AST-seal-clean. Note: working tree at start contained other Phase 8 plans' uncommitted artifacts (08-02, 08-04, 08-05); those have since landed in their own commits (`815ca89`, `25a9165`, `47307d1`, `3888ac5`) — not authored by this plan executor.
Resume hook: Plan 08-06 (registration) can now wire multi_agent + self_consistency into HARNESSES_BY_TASK_TYPE alongside other Wave-2/3 harnesses. Plan 08-07 (freeze-tag move) must wait for ALL Wave-2/3 plans to land. Plan 08-05 has a known AST-seal violation on streaming_react.py — see deferred-items.md.
