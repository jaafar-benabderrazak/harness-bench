---
phase: 08-expand-harness-family
plan: 07
subsystem: methodology-freeze
tags: [freeze-tag, manifest, methodology, phase-8]
requires:
  - 08-06 (registration of all 16 harnesses + AST-seal relaxation)
provides:
  - harnesses-frozen tag at post-Phase-8 commit (2af30fc)
  - HARNESSES_FROZEN.md updated with 4th tag-move row + 20-entry per-file SHA table
affects:
  - downstream Plan 08-08 (article refresh) — now unblocked pending user-triggered matrix re-runs
tech-stack:
  added: []
  patterns:
    - "force tag move via `git tag -f` + `git push --force origin <tag>` after sanity gate"
    - "manifest commit precedes tag move so the tag anchors on the manifest itself"
key-files:
  created:
    - .planning/phases/08-expand-harness-family/08-07-SUMMARY.md
  modified:
    - HARNESSES_FROZEN.md (committed at 2af30fc)
decisions:
  - "Tag now anchors on the manifest commit itself (2af30fc), not on a separate post-manifest commit. The manifest IS the freeze record, so co-locating it with the tag eliminates a needless trailing 'docs only' commit."
  - "Force-push of the tag was authorized by the user. The previous tag SHA (9977e85) is preserved in the HARNESSES_FROZEN.md tag-moves table row."
metrics:
  duration: ~6 min (continuation execution)
  completed: 2026-04-25
---

# Phase 8 Plan 07: Freeze-Tag Move Summary

Moved the `harnesses-frozen` git tag from `9977e85` to `2af30fc` (the post-Phase-8 commit containing the 16-harness registry + run_python tool + per-call temperature kwarg + manifest update), force-pushed to origin, and confirmed downstream gate is green.

## Tag move recorded

| Field | Value |
|-------|-------|
| Prior tag SHA | `9977e85` (Phase 6 backend pivot + code-gen baseline) |
| New tag SHA | `2af30fc` (Phase 8 expansion + manifest update) |
| Reason | Phase 8 harness expansion: 8 new harnesses + run_python tool + temperature kwarg + per-harness control-flow tests |
| Tests at new tag | **87/87 GREEN** (`pytest -q` 12.27s) |
| Matrix runs invalidated | None (no matrix had been executed against the prior tag with the expanded registry) |
| Push confirmation | `+ 9977e85...2af30fc harnesses-frozen -> harnesses-frozen (forced update)` |

## 20-entry per-file blob SHA table at the new tag

Authoritative table is in `HARNESSES_FROZEN.md` (committed in `2af30fc`). Reproduced here for self-containment:

| Path | Blob SHA |
|------|----------|
| `src/harness_eng/harnesses/base.py` | `7edfe0d83b3721314819a66b03f94ecdb25141c6` |
| `src/harness_eng/harnesses/single_shot.py` | `d1dae663d1f0d39cd77f1dd95e9d8c1ee9e83856` |
| `src/harness_eng/harnesses/react.py` | `3e0f63424ab0dd9e9b76b83833b92ee2631a913a` |
| `src/harness_eng/harnesses/plan_execute.py` | `71f07f0af510fe6b9121a8892fa23ff994d99fec` |
| `src/harness_eng/harnesses/reflexion.py` | `424c6dc71a79dccca0cb930d1e095f7f4c5b154c` |
| `src/harness_eng/harnesses/minimal.py` | `eeaf67d89c0de36f3c1ffe953f4109ccbb45ed0e` |
| `src/harness_eng/harnesses/chain_of_thought.py` | `139c18d592e83f269dcfdc432bc8f138c5c2c2ef` |
| `src/harness_eng/harnesses/test_driven.py` | `713177e3d59597376f3f29a854e016c21d758a91` |
| `src/harness_eng/harnesses/retry_on_fail.py` | `54785816b04056bafc3edd374a23659b5e8f74e5` |
| `src/harness_eng/harnesses/tree_of_thoughts.py` | `76147b6f4ad9b6ccd83cbb69a4af7dc898a3b172` |
| `src/harness_eng/harnesses/multi_agent.py` | `debeaf3ce27943c1bb041836f5c248b1111b32cc` |
| `src/harness_eng/harnesses/react_with_replan.py` | `0a7646896b491471f73d72dffd9e493906a8f24a` |
| `src/harness_eng/harnesses/self_consistency.py` | `0c113d30e7e26fcbf0e109828a6189ee0f6405f1` |
| `src/harness_eng/harnesses/program_aided.py` | `4992b8fb1a21b61a307ce21072cd286aeee019fa` |
| `src/harness_eng/harnesses/tool_use_with_validation.py` | `6a9db4795dab97eeabe4ffbc20863bc41fe005f8` |
| `src/harness_eng/harnesses/streaming_react.py` | `f1b8a706bc21d0bf78ebdb9fb14befdccc1c9e2c` |
| `src/harness_eng/harnesses/cached_react.py` | `599a99d5b5102ca0adf08a42ba12e017f8224a8f` |
| `src/harness_eng/harnesses/__init__.py` | `9da8bf9f17edafd1b6ee407d34244267f4ba0f38` |
| `src/harness_eng/tools.py` | `d099ea4ce41dd124df451730108c64202ec517d2` |
| `src/harness_eng/model.py` | `f1ce85e7e4efcab50c0a76b1619cdd53fe9f368a` |

## Streaming_react narrative outcome

Per `08-05-VERIFY.md` outcome **FAIL** (Ollama OOM: glm-4.7-flash declares 23.4 GiB system memory; host has 6.9 GiB available). The harness file lives in tree at SHA `f1b8a706` with full Anthropic streaming + Ollama per-chunk aggregation, and is registered in the `HARNESSES` dict, but is **EXCLUDED** from `HARNESSES_BY_TASK_TYPE`. Matrix membership at the freeze tag:

- `html_extract`: 11 harnesses (excludes streaming_react)
- `code_gen`: 9 harnesses

Re-enable path: re-run `scripts/verify_streaming_ollama.py`, update `08-05-VERIFY.md` to PASS, restart Python — the dynamic `_streaming_ok()` check in `harnesses/__init__.py` reads the verify-doc at import time. No code change to gated files needed.

## Operations executed

### Operation 1 — local tag move

```bash
git tag -f harnesses-frozen 2af30fc
# Updated tag 'harnesses-frozen' (was 9977e85)
```

Sanity gate (all 4 PASS):

| Check | Result |
|-------|--------|
| Tag SHA == `2af30fcc9786cd152c6bb599c2f0240fd7c1e01c` | PASS |
| `git diff --name-only harnesses-frozen HEAD -- <gated paths>` | PASS (empty) |
| `python -c "from harness_eng.runner import check_freeze_gate; check_freeze_gate()"` | PASS (exit 0, no exception) |
| `pytest -q` | PASS (87 passed in 12.27s) |

### Operation 2 — force-push to origin

```bash
git push --force origin harnesses-frozen
# To https://github.com/jaafar-benabderrazak/harness-bench.git
#  + 9977e85...2af30fc harnesses-frozen -> harnesses-frozen (forced update)
```

### Push of main (manifest commit 2af30fc)

```bash
git push origin main
# To https://github.com/jaafar-benabderrazak/harness-bench.git
#    21f4193..2af30fc  main -> main
```

## Test count at the new tag

**87/87 passing** at `2af30fc`. No regressions from the tag move (the move is metadata-only — it did not touch tree).

## Reminder for next plan (08-08)

Plan 08-08 (article refresh) is **BLOCKED on user-triggered matrix re-runs**:

- HTML matrix: `python scripts/run_full.py --seeds 3 --yes` (~2h on local CPU + glm-4.7-flash, 11 harnesses × 5 fixtures × 3 seeds = 165 trials)
- Code-gen matrix: `python scripts/run_code_benchmark.py --seeds 3 --yes` (~1h, 9 harnesses × 5 fixtures × 3 seeds = 135 trials)

These produce `runs/<id>/` outputs that Plan 08-08 (article refresh) consumes. **DO NOT auto-run these** — per CONTEXT cross-cutting decision, matrix runs are user-triggered.

After both matrix runs land, Plan 08-08 will:

1. Refresh `writeup/article.md` numbers from new `summary.csv`
2. Add the streaming_react Ollama-OOM exclusion narrative to the article's "honest scope" section
3. Update the Phase 8 frontier chart with all 16 harnesses (or 11/9 by task type)
4. Mark requirement ART-05 complete in REQUIREMENTS.md

## Deviations from Plan

None. The two-operation sequence (local tag move, then force-push) executed cleanly. All four post-move sanity checks passed first try. No auto-fix rules triggered.

## Self-Check: PASSED

- FOUND: `.planning/phases/08-expand-harness-family/08-07-SUMMARY.md` (this file)
- FOUND: commit `2af30fc` (manifest update)
- FOUND: tag `harnesses-frozen` at `2af30fcc9786cd152c6bb599c2f0240fd7c1e01c`
- FOUND: remote tag at `2af30fc` (push confirmed: `+ 9977e85...2af30fc harnesses-frozen -> harnesses-frozen (forced update)`)
- FOUND: remote main at `2af30fc` (push confirmed: `21f4193..2af30fc main -> main`)
- VERIFIED: gated-file diff vs new tag is empty
- VERIFIED: `check_freeze_gate()` exits 0
- VERIFIED: pytest 87/87 passing at the new tag
