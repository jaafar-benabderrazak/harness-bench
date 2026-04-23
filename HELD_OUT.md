---
layout: default
title: Held-Out Fixtures — Decision
---

# Held-Out Fixtures — Decision

## Decision

**Option A — No hold-out.** All five fixtures (`product_01`, `job_01`, `event_01`, `recipe_01`, `paper_01`) are used during harness development AND in the matrix run. Nothing is held out.

## Rationale

1. **The benchmark is a pilot, not a published benchmark.** The portfolio piece's value is in the methodology (harness-as-variable, frozen-model seal, tamper-evident freeze tag, deterministic grader, honest cost accounting) — not in generalization claims over an unseen test set. Holding out 1 of 5 (20%) or 2 of 5 (40%) materially reduces the already-small dev sample without proportionally improving article credibility.

2. **The methodology story is tight without it.** Article claims are scoped to "on this 5-task suite, under this frozen model, with these five harnesses, the spread was X." Adding "and we held out N examples to verify" adds a sentence and a small CI improvement, but the reader's confidence is mostly gained from the harness freeze tag + the trace viewer + the open repo.

3. **The harness-freeze gate (Phase 2) is the structural defense against the peek-and-patch pitfall**, not a held-out set. You cannot edit a harness after freeze and rerun; the runner refuses. That's the discipline.

4. **The v1.x / v2 roadmap path for generalization is already documented.** `.planning/REQUIREMENTS.md` → v2 SCALE-02 explicitly lists "Add 2 held-out fixtures never used during harness iteration" as deferred scope. Expanding from 5 to 40 tasks (SCALE-01) is the more interesting move for generalization; held-outs are a cheap add on top of that later.

## Implications

- All 5 fixtures are visible to the author during harness implementation.
- The Phase 2 `harnesses-frozen` tag is the sole mechanism preventing "peek-and-patch" contamination.
- The article's "honest scope" section must state plainly: 5 tasks, no held-outs, generalization claims scoped to this suite.
- If v2 is pursued, SCALE-02 (hold out 2 of 40) becomes load-bearing because the matrix size makes generalization claims more natural.

---
*Decision recorded: 2026-04-23 — committed before Phase 2 harnesses-frozen tag.*
