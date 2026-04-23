# Harness Freeze Manifest

**Freeze date:** 2026-04-23
**Freeze commit SHA:** resolve with `git rev-parse harnesses-frozen` (tag pins an exact commit; self-referencing the SHA in this file is a chicken-and-egg problem, so the tag is the source of truth)
**Git tag:** `harnesses-frozen`

## Why this exists

The entire experiment depends on one invariant: the five harnesses, their shared tool dispatcher, and the single-import-site model client cannot be edited after results are seen. Without this discipline, the comparison is invalid — the classic "peek-and-patch" failure mode. The `harnesses-frozen` git tag plus the runner's `check_freeze_gate()` pre-flight make this discipline structural rather than procedural.

## Gated paths (runner refuses to execute if any of these have diverged from the tag)

- `src/harness_eng/harnesses/`
- `src/harness_eng/tools.py`
- `src/harness_eng/model.py`

## Per-file blob SHAs at freeze commit

| Path | Blob SHA |
|------|----------|
| `src/harness_eng/harnesses/base.py` | `625ac6abb31c0b62e7af9dcf33c92279a9707c4f` |
| `src/harness_eng/harnesses/single_shot.py` | `0b2aa16e412122ebca0ca7ac1ab66e5c41527ce5` |
| `src/harness_eng/harnesses/react.py` | `2923e22ed7cf0da8e4620ed346f4eaaf0fae67f9` |
| `src/harness_eng/harnesses/plan_execute.py` | `8740421ed48d0673f1e792a6a104508cba816097` |
| `src/harness_eng/harnesses/reflexion.py` | `57586a286a8628ef28234703ba856fe8845f467a` |
| `src/harness_eng/harnesses/minimal.py` | `6ccb0f9e604bb9bd604b2ba1d1cbb7a4ba1716c7` |
| `src/harness_eng/tools.py` | `fddabd878b3314965074b231b5e75ed0dfd278c1` |
| `src/harness_eng/model.py` | `7315affee23e2bf9d94f2484fb3c8783756f9637` |

## Tag moves

| Date | From SHA | To SHA | Reason | Invalidated matrix runs |
|------|----------|--------|--------|------------------------|
| 2026-04-23 | `0a44719` | `4eacafb` | Phase 4 added `TOOL_WHITELIST` attrs to every harness class + enforcement in `_step_model`. No matrix had been executed against the prior tag, so the move is a mechanical re-anchor — nothing is invalidated. | None |
| 2026-04-23 | `4eacafb` | `d0fc1f1` | CI-fix cleanup: removed unused `field` import from `harnesses/base.py`. No runtime behavior change, but blob SHA changes, so the tag re-anchors. Still no matrix runs invalidated. | None |
| 2026-04-23 | `d0fc1f1` | (this commit) | Backend pivot: added Ollama support in `model.py` so the experiment can run on a free local model (mistral:7b by default). Gated file changed; tag re-anchors onto the new code path. Still no matrix runs invalidated. | None |

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
