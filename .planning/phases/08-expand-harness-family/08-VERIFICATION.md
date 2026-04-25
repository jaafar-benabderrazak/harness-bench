---
phase: 08-expand-harness-family
verified: 2026-04-24T00:00:00Z
status: passed
score: 12/12 must-haves verified (under documented qualitative-only scope pivot)
scope_pivot:
  acknowledged: true
  reason: "Original Phase 8 goal called for re-running the full matrix on the expanded set. Hardware (3.3-6.5 GiB free) cannot host glm-4.7-flash (declares 23.4 GiB working set); mistral:7b smoke = 0/5 (below tool-use floor). Plan 08-08 was pivoted to QUALITATIVE-only article refresh. Article header + footer + dedicated methodology section dual-cite both freeze SHAs (9977e85 prior, 2af30fc current) and explicitly disclaim 'implemented but not yet matrix-validated'."
  unmet_original_criteria:
    - id: 5
      text: "Both matrices re-run end-to-end via run_full.py and run_code_benchmark.py"
      reason: "Hardware OOM — out of scope for this article refresh; freeze tag at 2af30fc anchors a future rerun"
    - id: 6_partial
      text: "Numerical findings folded into Part 1 and Part 2 tables"
      reason: "Qualitative-only — Part 1/Part 2 tables intentionally retain 2026-04-23 8-harness numbers from prior tag; explicit signposting in article that the 8 new harnesses are not in the numerical tables"
    - id: 8
      text: "Dollar-extrapolation table recomputed against new token-cost rows for the expanded set"
      reason: "No new token-cost data — same blocker as #5"
human_verification:
  - test: "Open writeup/article-medium.html in a browser; confirm 18 PNG diagrams render in order; confirm 8 new harness blocks have visible Mermaid-rendered diagram images; confirm framework-mapping bullets read cleanly with paper citations"
    expected: "All sections render; 18 diagram PNG images visible (10 prior + 8 new harness diagrams); no broken image references; layout is clean"
    why_human: "Visual rendering of HTML and PNG embedding is not programmatically verifiable — file presence + grep counts cannot confirm the page renders correctly in a browser"
  - test: "Read writeup/article.md sections lines 262-520 end-to-end; confirm the qualitative descriptions are accurate to your reading of the harness implementations and that the Phase 8 methodology disclaimer reads as honest scope, not deflection"
    expected: "Each per-harness block accurately maps to the implementation; methodology section frames the constraint as transparent disclosure, not excuse"
    why_human: "Prose accuracy and tone are author judgment — automated checks confirmed presence + structure but not editorial fidelity"
---

# Phase 8: Expand Harness Family + Refresh Article — Verification Report

**Phase Goal (original ROADMAP):** "The harness library expands from 8 to 16 distinct strategies, each mapping to a recognizable agent pattern (CrewAI, AutoGen, ToT-paper, PaL-paper, self-consistency, retry-with-replan, streaming-early-termination, tool-result-caching). The full matrix re-runs on the expanded set under a new `harnesses-frozen` tag move. The article and Medium HTML are updated to integrate every new harness into the per-harness description block, framework-mapping section, and findings tables."

**Verified:** 2026-04-24
**Status:** passed (with documented scope pivot for matrix-rerun + dollar-extrapolation; article truthfully reflects the constraint)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                                              | Status     | Evidence                                                                                                                 |
| --- | ------------------------------------------------------------------------------------------------------------------ | ---------- | ------------------------------------------------------------------------------------------------------------------------ |
| 1   | 8 new harness files exist with `name`, `TOOL_WHITELIST` (frozenset), and `_execute`; each is substantive (≥60 lines)| ✓ VERIFIED | All 8 files present (68–249 lines each); `len(HARNESSES) == 16`; class-attr probe confirms `name` + `TOOL_WHITELIST`     |
| 2   | All 16 harnesses are importable through `harness_eng.harnesses` package and the AST seal passes (no module-level anthropic imports) | ✓ VERIFIED | `from harness_eng.harnesses import HARNESSES` succeeds; `^import anthropic|^from anthropic` grep on harnesses/ → 0 hits  |
| 3   | `HARNESSES_BY_TASK_TYPE` membership reflects per-task-type design; `streaming_react` is in HARNESSES dict but excluded from both task-type lists per 08-05-VERIFY.md FAIL outcome | ✓ VERIFIED | `html_extract`=11 (excludes streaming_react), `code_gen`=9; `streaming_react in HARNESSES` = True; both task lists exclude it |
| 4   | `run_python` tool added with 5s subprocess timeout, registered in `TOOL_IMPLS` + `TOOL_SCHEMAS`                    | ✓ VERIFIED | `_tool_run_python` def at tools.py:108; entries in `TOOL_IMPLS` (line 139) + `TOOL_SCHEMAS` (line 181)                   |
| 5   | `model.call()` accepts optional `temperature` kwarg overriding `CONFIG.model.temperature`; threaded through both Anthropic + Ollama paths | ✓ VERIFIED | model.py:39-45 + 66/72 Anthropic + 208/215 Ollama; pytest covers both default + override paths                            |
| 6   | `Harness._step_model` accepts and forwards `temperature` kwarg                                                     | ✓ VERIFIED | base.py:159 signature + line 174 trace event + line 176 forward to `model_call(... temperature=temperature)`             |
| 7   | `cached_react` cache is a LOCAL variable in `_execute`, not a `self` attribute (cell-scoped guarantee)             | ✓ VERIFIED | cached_react.py:39 `cache: dict[tuple[str, str], str] = {}` inside `_execute`; AST + grep confirm no `self.cache`/`self._cache` |
| 8   | `jsonschema>=4.20.0` is a runtime dependency; `tool_use_with_validation` uses `Draft202012Validator` with `MAX_VALIDATION_RETRIES=3` and `stop_reason='schema_validation_exhausted'` | ✓ VERIFIED | pyproject.toml:15; tool_use_with_validation.py contains both patterns; tests verify the 3-strikes path                  |
| 9   | Freeze tag `harnesses-frozen` moved forward to a single commit AFTER all 8 new harnesses + tools.py + model.py + base.py merged | ✓ VERIFIED | `git rev-parse harnesses-frozen` = `2af30fcc9786cd152c6bb599c2f0240fd7c1e01c`; `git diff harnesses-frozen HEAD -- <gated>` is EMPTY; HARNESSES_FROZEN.md tag-moves table has the 9977e85 → 2af30fc row with reason "Phase 8 harness expansion" |
| 10  | Runner pre-flight `check_freeze_gate()` passes against the new tag; full pytest suite green                       | ✓ VERIFIED | `python -c "from harness_eng.runner import check_freeze_gate; check_freeze_gate()"` exits 0; `pytest -q` = **87 passed in 13.62s** |
| 11  | `writeup/article.md` has per-harness description blocks for all 8 new harnesses (what-it-does / in-production / strengths / weaknesses / use-when / Mermaid diagram); framework-mapping section cites Yao 2023, Wang 2022, Gao 2022, CrewAI/AutoGen/LangGraph, Pydantic-style, streaming early-termination, in-memory memoization, loop-detection | ✓ VERIFIED | 8 `#### <harness>` headers (lines 272–461); framework mapping at lines 491–498; structure matches existing 8-harness template |
| 12  | `writeup/article-medium.html` regenerated; 18 diagram PNGs in writeup/diagrams/; both freeze SHAs (9977e85 + 2af30fc) cited in header byline + dedicated methodology section + footer; article honestly disclaims "implemented but not yet matrix-validated" rather than claiming a matrix rerun was done | ✓ VERIFIED | `tree_of_thoughts` etc. appear 26× in article.md, 26× in article-medium.html; freeze SHA citations: 7× in article.md, 7× in HTML; methodology section at lines 506–520 explicitly explains the qualitative-only scope; line 23 header dual-cites; line 825 footer dual-cites |

**Score:** 12/12 truths verified (under documented qualitative-only scope pivot — see `scope_pivot` block in frontmatter)

### Required Artifacts

| Artifact                                                          | Expected                                                                                       | Status     | Details                                                                                              |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------- |
| `src/harness_eng/harnesses/tree_of_thoughts.py`                  | TreeOfThoughtsHarness with heuristic candidate scoring; ≥60 lines                              | ✓ VERIFIED | 108 lines; `_score_candidate` formula `n / max(avg_len, 1.0)`; whitelist `{css_select, submit_answer}` |
| `src/harness_eng/harnesses/multi_agent.py`                       | MultiAgentHarness with 3 distinct system prompts + isolated histories; UNION TOOL_WHITELIST    | ✓ VERIFIED | 168 lines; PLANNER/EXECUTOR/CRITIC; isolated `messages` lists; whitelist 6 tools (HTML ∪ code-gen)   |
| `src/harness_eng/harnesses/react_with_replan.py`                 | ReActWithReplanHarness with two-NO_MATCH-same-selector replan trigger                          | ✓ VERIFIED | 90 lines; `replan_triggered` event emitted; HTML whitelist                                          |
| `src/harness_eng/harnesses/self_consistency.py`                  | SelfConsistencyHarness, N=5 samples at temperature=0.7; per-field majority HTML, AST-normalized code | ✓ VERIFIED | 147 lines; `N_SAMPLES=5`, `SAMPLE_TEMPERATURE=0.7`; both task types                                  |
| `src/harness_eng/harnesses/program_aided.py`                     | ProgramAidedHarness, code-gen-only, uses `run_python` tool                                     | ✓ VERIFIED | 68 lines; rejects HTML cleanly with `no_submit`; whitelist `{run_python, submit_answer}`             |
| `src/harness_eng/harnesses/tool_use_with_validation.py`          | jsonschema-validates every non-submit call; 3 strikes → `schema_validation_exhausted`          | ✓ VERIFIED | 117 lines; `Draft202012Validator` pre-built per tool; `MAX_VALIDATION_RETRIES=3`                     |
| `src/harness_eng/harnesses/streaming_react.py`                   | Streaming impl with mid-stream submit_answer detection; deferred SDK imports                   | ✓ VERIFIED | 249 lines; both Anthropic + Ollama streaming paths; deferred imports inside methods (passes ast-walk seal) |
| `src/harness_eng/harnesses/cached_react.py`                      | Cell-scoped local-variable cache; no `self.cache`                                              | ✓ VERIFIED | 96 lines; `cache: dict[tuple[str, str], str] = {}` is a function-local at line 39                    |
| `src/harness_eng/tools.py`                                        | `_tool_run_python` impl + `TOOL_IMPLS` + `TOOL_SCHEMAS` entries                                | ✓ VERIFIED | All three locations confirmed                                                                        |
| `src/harness_eng/model.py`                                        | `temperature: float \| None = None` kwarg threaded through both backends                       | ✓ VERIFIED | All three required edit sites confirmed                                                              |
| `src/harness_eng/harnesses/base.py`                               | `_step_model` accepts + forwards temperature; trace event records it                           | ✓ VERIFIED | base.py:159, 174, 176                                                                                |
| `src/harness_eng/harnesses/__init__.py`                           | 16-harness registry; conditional streaming_react via `_streaming_ok()` reading 08-05-VERIFY.md | ✓ VERIFIED | 92 lines; `len(HARNESSES) == 16`; conditional logic at lines 70-90                                  |
| `src/harness_eng/analysis.py` (HARNESS_COLORS)                   | All 16 harness names with distinguishable hex; `.get(name, fallback)` consumption              | ✓ VERIFIED | `HARNESS_COLORS` dict has 16 entries; analysis code uses `.get(row["harness"], "#374151")` (5 sites) |
| `pyproject.toml`                                                  | jsonschema>=4.20.0 in `[project] dependencies`                                                 | ✓ VERIFIED | Line 15                                                                                              |
| `HARNESSES_FROZEN.md`                                             | New tag-move row at 2af30fc; 20-entry per-file blob SHA table                                  | ✓ VERIFIED | Tag-moves table row 4 (2026-04-25, 9977e85 → "this commit", "Phase 8 harness expansion"); 20-row SHA table at lines 25-45 |
| `.planning/phases/08-expand-harness-family/08-05-VERIFY.md`      | streaming_react Ollama compatibility outcome                                                   | ✓ VERIFIED | Outcome: FAIL (Ollama OOM 23.4 GiB > 6.9 GiB); implication: register with task_type=[]               |
| `writeup/article.md`                                              | 8 new harness blocks + framework mapping + dual-SHA citations + qualitative-only methodology   | ✓ VERIFIED | 827 lines; 8 #### blocks (lines 272-461); framework mapping (lines 487-498); methodology (506-520)   |
| `writeup/article-medium.html`                                     | Regenerated; reflects expanded harness set; 18 PNG diagrams referenced                         | ✓ VERIFIED | 606 lines (regenerated); 26 occurrences of new harness names; 7 freeze SHA citations                 |
| `writeup/diagrams/` (8 new Mermaid sources + 9 new PNGs)         | One .md per new harness; rendered PNGs                                                         | ✓ VERIFIED | 8 .md sources (tree_of_thoughts.md … cached_react.md); 18 PNGs in diagrams/                          |
| `tests/` (per-harness control-flow tests)                         | New tests + registry/allowlist updates                                                         | ✓ VERIFIED | `pytest -q` reports **87 passed** (was 41 pre-Phase-8; +46 new tests across Plans 01-06)             |

### Key Link Verification

| From                                                       | To                                                                | Via                                       | Status      | Details                                                                  |
| ---------------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------- | ----------- | ------------------------------------------------------------------------ |
| `harnesses/__init__.py::HARNESSES`                         | 8 new harness class imports                                       | module-level imports + dict registration  | ✓ WIRED     | All 8 imports + dict entries present at lines 5-20 + 33-41               |
| `harnesses/__init__.py::HARNESSES_BY_TASK_TYPE`            | streaming_react conditional via 08-05-VERIFY.md                   | `_streaming_ok()` reads outcome at import | ✓ WIRED     | Function reads file; FAIL → not appended; html_extract has 11 (excludes streaming_react) |
| `harnesses/base.py::_step_model`                           | `model.py::call`                                                  | keyword argument `temperature`            | ✓ WIRED     | `model_call(system, messages, tools, temperature=temperature)` at base.py:176 |
| `tools.py::TOOL_IMPLS`                                     | `_tool_run_python`                                                | registry lookup                           | ✓ WIRED     | Line 139: `"run_python": _tool_run_python,`                              |
| `tools.py::TOOL_SCHEMAS`                                   | run_python schema entry                                           | registry lookup                           | ✓ WIRED     | Line 181: `"run_python": { ... "input_schema": ... }`                    |
| `tool_use_with_validation.py`                              | `tools.py::TOOL_SCHEMAS`                                          | per-tool Draft202012Validator pre-build   | ✓ WIRED     | `_VALIDATORS = { name: Draft202012Validator(schema["input_schema"]) for name, schema in TOOL_SCHEMAS.items() }` |
| `program_aided.py`                                         | `tools.py::run_python`                                            | `build_tool_list(['run_python', 'submit_answer'])` | ✓ WIRED     | Tool name appears in PROGRAM_AIDED_TOOLS; whitelist enforces it          |
| `cached_react.py::_execute`                                | function-local `cache: dict[tuple[str, str], str] = {}`           | function-scope local (NOT self.cache)     | ✓ WIRED     | Line 39 confirms structural guarantee; AST seal test enforces it         |
| `streaming_react.py`                                       | Anthropic SDK streaming context manager                           | deferred import inside method body         | ✓ WIRED     | `from anthropic import Anthropic` at module-method level (passes ast-walk seal in test_harness_registry) |
| `HARNESSES_FROZEN.md` tag-moves table                      | `git tag harnesses-frozen` at 2af30fc                             | matching from-SHA / to-SHA                | ✓ WIRED     | Row 4 explicitly cites 9977e85 → 2af30fc with reason "Phase 8 harness expansion" |
| `HARNESSES_FROZEN.md` per-file SHA table                   | `git ls-tree harnesses-frozen src/harness_eng/...`                | blob SHA equality                         | ✓ WIRED     | 20-row table; per-file blob SHAs match the SUMMARY 08-07 table verbatim   |
| `writeup/article.md` numerical Part 1 + Part 2 tables      | `runs/<latest>/summary.csv` from prior tag (`9977e85`)            | preserved-from-prior-run interpolation     | ✓ WIRED (prior tag) | Article header line 23 + footer line 825 dual-cite both SHAs; no claim of new matrix run |
| `writeup/article-medium.html`                              | `writeup/article.md`                                              | `scripts/build_medium_html.py`            | ✓ WIRED     | HTML regenerated 2026-04-25 23:06; contains all 8 new harness names + 7 SHA citations |

### Requirements Coverage

| Requirement | Source Plan(s)                  | Description                                                                                       | Status         | Evidence                                                                                                                       |
| ----------- | ------------------------------- | ------------------------------------------------------------------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| HARN-08     | 08-02, 08-06, 08-07             | `tree_of_thoughts` harness — toolless propose-3, deterministic heuristic scoring                  | ✓ SATISFIED    | tree_of_thoughts.py present, registered in HARNESSES + HARNESSES_BY_TASK_TYPE['html_extract'], tests green                     |
| HARN-09     | 08-03, 08-06, 08-07             | `multi_agent` — 3 isolated histories, Handoff dict, UNION whitelist                                | ✓ SATISFIED    | multi_agent.py present, registered in both task types, isolated-histories test green                                            |
| HARN-10     | 08-02, 08-06, 08-07             | `react_with_replan` — replan after 2× NO_MATCH same selector                                      | ✓ SATISFIED    | react_with_replan.py present, `replan_triggered` event verified by control-flow test                                           |
| HARN-11     | 08-01, 08-03, 08-06, 08-07      | `self_consistency` — N=5 samples at T=0.7; per-field HTML, AST-normalized code                    | ✓ SATISFIED    | self_consistency.py present; temperature=0.7 verified by test; both task types                                                  |
| HARN-12     | 08-01, 08-04, 08-06, 08-07      | `program_aided` — code-gen-only via `run_python` tool                                              | ✓ SATISFIED    | program_aided.py present; `run_python` invoked; html_extract task rejection test green                                          |
| HARN-13     | 08-01, 08-04, 08-06, 08-07      | `tool_use_with_validation` — jsonschema; 3 strikes → schema_validation_exhausted                  | ✓ SATISFIED    | tool_use_with_validation.py present; `MAX_VALIDATION_RETRIES=3`; stop_reason verified by test                                  |
| HARN-14     | 08-05, 08-06, 08-07             | `streaming_react` — verified-out-of-band; `task_type=[]` per 08-05-VERIFY FAIL                    | ✓ SATISFIED    | streaming_react.py present; in HARNESSES; absent from both task-type lists; HARNESSES_FROZEN.md documents Ollama OOM            |
| HARN-15     | 08-02, 08-06, 08-07             | `cached_react` — local-variable cache scoped to `_execute`                                         | ✓ SATISFIED    | cached_react.py present; cache is function-local at line 39; `test_cache_does_not_leak_across_cells` passes                    |
| BENCH-06    | 08-06                           | Phase 8 harnesses integrated into the matrix via HARNESSES_BY_TASK_TYPE                            | ✓ SATISFIED    | html_extract: 11 harnesses; code_gen: 9 harnesses; streaming_react excluded per Ollama OOM                                      |
| RUN-07     | 08-06                           | `_step_model` enforces per-harness TOOL_WHITELIST for all 16; UNION whitelists covered            | ✓ SATISFIED    | base.py:163-170 subset check on every model call; tests verify multi_agent + tool_use_with_validation UNIONs                   |
| ANAL-06    | 08-06                           | HARNESS_COLORS palette covers all 16; `.get(name, fallback)` consumption                          | ✓ SATISFIED    | All 16 names in dict; `.get` with `#374151` fallback at 5 call sites                                                            |
| ART-05     | 08-08 (qualitative-only)        | Article refresh covers expanded harness family; ART-05 marked Complete in REQUIREMENTS.md         | ✓ SATISFIED    | 8 new per-harness blocks + framework mapping + dual-SHA citations + dedicated methodology section explaining the qualitative-only scope |

**12/12 requirements satisfied** (subject to the documented scope pivot for ART-05's numerical-table component, addressed by explicit article disclaimer rather than fabricated numbers).

No orphaned requirements. No requirement IDs from plan frontmatter unaccounted for in REQUIREMENTS.md.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
| ---- | ------- | -------- | ------ |
| (none) | TODO/FIXME/XXX/HACK/placeholder/coming-soon scan on `src/harness_eng/harnesses/` | — | No anti-patterns found |
| (none) | Module-level `import anthropic` / `from anthropic` outside model.py and method-body deferred imports | — | AST seal in `tests/test_harness_registry.py::test_no_harness_imports_anthropic_at_module_level` enforces structurally |
| (none) | `self.cache` / `self._cache` on cached_react | — | Grep returns 0 hits — cache is structurally local, test asserts no `cache` attribute on instance |

`return None` occurrences in self_consistency.py + tool_use_with_validation.py + single_shot.py are all legitimate exit branches in valid extract methods (e.g., when no `tool_use` block matches the expected name); not stub returns. `pass` in base.py:68 is the abstract-method body — legitimate.

### Honest-Scope Audit (does the article claim a matrix rerun happened?)

| Location | Excerpt | Honest? |
| -------- | ------- | ------- |
| Line 23 (header byline) | "Numerical results in Part 1 and Part 2 are from `glm-4.7-flash` against freeze tag `9977e85` on 2026-04-23. Freeze tag has since moved to `2af30fc` (16-harness expansion — see 'Phase 8 expansion' below); the new harnesses are implemented and tested but not yet matrix-validated on this hardware." | ✓ HONEST — explicitly disclaims new matrix run |
| Line 266 (Phase 8 expansion intro) | "**These 8 are NOT numerically benchmarked in this article.** … the matrix re-run on this hardware is gated on a memory ceiling that the current model cannot clear." | ✓ HONEST |
| Line 502 (after framework mapping) | "Future numerical work against the freeze tag `2af30fc` would extend Part 1 and Part 2 tables to cover this expanded set." | ✓ HONEST — uses conditional "would" |
| Lines 506-520 (dedicated methodology section) | Explains Ollama OOM (23.4 GiB declared vs 6.9 GiB available), mistral:7b 0/5 smoke, why a uniform-zero matrix would mislead, what a future practitioner with stronger hardware can do | ✓ HONEST — full transparency |
| Line 825 (footer) | "Freeze tag at article-publish time: `9977e85` (numbers in Part 1 + Part 2 from this tag). Current freeze tag: `2af30fc` (16-harness expansion; future matrix runs at this SHA produce comparable numbers for all 16 harnesses)." | ✓ HONEST — dual-cite |

**Result:** No location in the article claims that a fresh 16-harness matrix was run. The qualitative-only pivot is documented as a deliberate methodology choice (transparency over fabrication), not concealed.

### Human Verification Required

Two items flagged for human verification (visual + editorial). See `human_verification` block in frontmatter.

1. **Browser-render of article-medium.html**
   - Test: Open `writeup/article-medium.html` in a browser; confirm 18 PNG diagrams render in order; confirm 8 new harness blocks have visible Mermaid-rendered diagram images; confirm framework-mapping bullets read cleanly with paper citations.
   - Expected: All sections render; 18 diagram PNG images visible (10 prior + 8 new harness diagrams); no broken image references; layout is clean.
   - Why human: Visual rendering of HTML and PNG embedding is not programmatically verifiable.

2. **Editorial fidelity of qualitative blocks + methodology section**
   - Test: Read `writeup/article.md` lines 262-520 end-to-end; confirm the qualitative descriptions are accurate to your reading of the harness implementations and that the Phase 8 methodology disclaimer reads as honest scope, not deflection.
   - Expected: Each per-harness block accurately maps to the implementation; methodology section frames the constraint as transparent disclosure, not excuse.
   - Why human: Prose accuracy and tone are author judgment — automated checks confirmed presence + structure but not editorial fidelity.

### Gaps Summary

**No gaps blocking the qualitative-only goal.**

The original ROADMAP success criteria 5 (matrix re-run) and 8 (dollar-extrapolation recompute) were not met because the host hardware (3.3-6.5 GiB free) cannot host glm-4.7-flash (declares 23.4 GiB working set), and a fallback model (mistral:7b) failed the tool-use floor on a 10-cell smoke test. Plan 08-08 was explicitly pivoted to QUALITATIVE-only with user authorization. The article HONESTLY documents this constraint at four locations (header, expansion intro, dedicated methodology section, footer); the freeze tag at `2af30fc` anchors a future practitioner's rerun against byte-identical harness code.

This satisfies the goal-backward verification standard: every code-side success criterion (1-7, partial 6) is fully met; the operational success criterion (5) and its dependent criterion (8) are deferred with documented constraints rather than concealed or fabricated. Per the verifier's instruction in this prompt: "The qualitative-only pivot for 08-08 should be classified as a documented scope reduction, not a gap, IF AND ONLY IF the article honestly reflects the constraint" — the article does, at four explicit locations, with no contradicting "matrix rerun done" claim anywhere in the prose.

### Hardware-Gated Future Work (not gaps for Phase 8)

These items are explicitly out of Phase 8 scope per the user-authorized pivot but should be tracked for a future plan:

1. Run `python scripts/run_full.py --seeds 3 --yes` against freeze tag `2af30fc` on hardware with ≥24 GiB free system memory.
2. Run `python scripts/run_code_benchmark.py --seeds 3 --yes` against the same tag.
3. Refresh Part 1 + Part 2 numerical tables in `writeup/article.md` from the new `summary.csv` files.
4. Recompute the dollar-extrapolation table at $2.50/M input + $10/M output frontier prices.
5. Re-publish article-medium.html.

The freeze tag at `2af30fc` ensures the harness code is byte-identical to the design intent the article describes — a future rerun produces directly comparable numbers.

---

*Verified: 2026-04-24*
*Verifier: Claude (gsd-verifier)*
