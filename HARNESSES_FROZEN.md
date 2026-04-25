---
layout: default
title: Harness Freeze Manifest
---

# Harness Freeze Manifest

**Freeze date:** 2026-04-25
**Freeze commit SHA:** resolve with `git rev-parse harnesses-frozen` (tag pins an exact commit; self-referencing the SHA in this file is a chicken-and-egg problem, so the tag is the source of truth)
**Git tag:** `harnesses-frozen`

## Why this exists

The entire experiment depends on one invariant: the harnesses, their shared tool dispatcher, and the single-import-site model client cannot be edited after results are seen. Without this discipline, the comparison is invalid — the classic "peek-and-patch" failure mode. The `harnesses-frozen` git tag plus the runner's `check_freeze_gate()` pre-flight make this discipline structural rather than procedural.

## Gated paths (runner refuses to execute if any of these have diverged from the tag)

- `src/harness_eng/harnesses/`
- `src/harness_eng/tools.py`
- `src/harness_eng/model.py`

## Per-file blob SHAs at freeze commit

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

## Tag moves

| Date | From SHA | To SHA | Reason | Invalidated matrix runs |
|------|----------|--------|--------|------------------------|
| 2026-04-23 | `0a44719` | `4eacafb` | Phase 4 added `TOOL_WHITELIST` attrs to every harness class + enforcement in `_step_model`. No matrix had been executed against the prior tag, so the move is a mechanical re-anchor — nothing is invalidated. | None |
| 2026-04-23 | `4eacafb` | `d0fc1f1` | CI-fix cleanup: removed unused `field` import from `harnesses/base.py`. No runtime behavior change, but blob SHA changes, so the tag re-anchors. Still no matrix runs invalidated. | None |
| 2026-04-23 | `d0fc1f1` | `9977e85` | Backend pivot: added Ollama support in `model.py` so the experiment can run on a free local model (glm-4.7-flash by default). Phase-6 follow-up also added the code-gen task type and three code-gen baseline harnesses (`chain_of_thought`, `test_driven`, `retry_on_fail`) plus a `single_shot` branch on `task.type` so it stops dumping HTML for code-gen tasks. Gated files changed; tag re-anchored onto the new code path. Matrix had been re-run against the new tag during Phase 6 article work; that run was not invalidated by this row (it produced the data the article cited). | None |
| 2026-04-25 | `9977e85` | (this commit) | Phase 8 harness expansion: added 8 new harnesses (`tree_of_thoughts`, `multi_agent`, `react_with_replan`, `self_consistency`, `program_aided`, `tool_use_with_validation`, `streaming_react`, `cached_react`); added `run_python` tool to `tools.py`; threaded per-call `temperature` kwarg through `model.call` and `Harness._step_model` (`base.py`); added `jsonschema` runtime dep. `streaming_react` is registered in the `HARNESSES` dict but EXCLUDED from `HARNESSES_BY_TASK_TYPE` per `.planning/phases/08-expand-harness-family/08-05-VERIFY.md` outcome **FAIL**: the configured Ollama backend cannot host glm-4.7-flash on this hardware (model declares 23.4 GiB system memory; host has 6.9 GiB available; failure mode differs from the predicted Ollama issue [#13840](https://github.com/ollama/ollama/issues/13840) post-tool-call halt but the registration implication is identical). Matrix membership: `html_extract`=11 harnesses, `code_gen`=9 harnesses. Per-harness control-flow tests added; full pytest suite 87/87 GREEN at the new tag. No matrix had been re-run against the prior tag with the expanded registry, so this move invalidates nothing — the matrix re-runs that follow this move (`scripts/run_full.py`, `scripts/run_code_benchmark.py`) are user-gated and produce the data the Phase 8 article refresh consumes. | None |

## What can still change post-freeze

- `src/harness_eng/runner.py` — the orchestration layer (adding seeds, manifests, tool-allowlist assertions) is outside the experimental control
- `src/harness_eng/analysis.py`, `src/harness_eng/trace_viewer.py` — read-only artifacts consuming the matrix output
- `src/harness_eng/cost_estimator.py`, `src/harness_eng/pricing.py` — estimation / cost math
- `src/harness_eng/config.py` — model id/temperature/max_tokens: not supposed to change, but not technically gated (change here would be visible in git history)
- `src/harness_eng/trace.py`, `src/harness_eng/grader.py` — already hardened in Phase 1; changes post-freeze are visible in git history

If any of the gated files need to change after freeze, the tag must be moved (which visibly invalidates the prior matrix run) and the article must document the reason. No quiet edits.

## Verification

At any time:

```bash
git diff harnesses-frozen HEAD -- src/harness_eng/harnesses/ src/harness_eng/tools.py src/harness_eng/model.py
```

An empty diff means the experiment is still valid. A non-empty diff either reflects a legitimate re-tag (with article-level justification) or a methodology violation.
