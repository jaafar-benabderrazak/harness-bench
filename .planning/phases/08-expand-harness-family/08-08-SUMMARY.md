---
phase: 08-expand-harness-family
plan: 08
subsystem: docs
tags: [article, medium-html, mermaid, methodology, freeze-tag]

# Dependency graph
requires:
  - phase: 08-07
    provides: "Freeze tag at 2af30fc with 16-harness manifest in HARNESSES_FROZEN.md"
provides:
  - "writeup/article.md with 8 new harness description blocks (qualitative-only)"
  - "writeup/article-medium.html regenerated, 18 PNG diagrams referenced"
  - "8 new Mermaid diagram source files in writeup/diagrams/"
  - "Methodology section explaining the qualitative-only scope and the matrix-rerun gating"
affects: [future-matrix-rerun, anthropic-backend-runs]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Article freeze-SHA dual-citation: numbers from prior tag (9977e85), structure from current tag (2af30fc)"
    - "Per-harness block template (what-it-does / in-production / strengths / weaknesses / use-when / Mermaid)"

key-files:
  created:
    - "writeup/diagrams/tree_of_thoughts.md"
    - "writeup/diagrams/multi_agent.md"
    - "writeup/diagrams/react_with_replan.md"
    - "writeup/diagrams/self_consistency.md"
    - "writeup/diagrams/program_aided.md"
    - "writeup/diagrams/tool_use_with_validation.md"
    - "writeup/diagrams/streaming_react.md"
    - "writeup/diagrams/cached_react.md"
    - "writeup/diagrams/diagram-10-ecfca6c7.png through diagram-18-00f0ae10.png"
  modified:
    - "writeup/article.md (+264 lines: Phase 8 expansion section + framework mapping + methodology note)"
    - "writeup/article-medium.html (regenerated, 64,414 bytes)"
    - ".planning/REQUIREMENTS.md (ART-05 marked Complete)"

key-decisions:
  - "Pivoted scope from full numerical refresh to qualitative-only: glm-4.7-flash declares 23.4 GiB, host has 6.9 GiB; mistral:7b smoke = 0/5 (below tool-use floor). A uniform-zero matrix would mislead more than inform."
  - "2026-04-23 Part 1 + Part 2 numbers preserved verbatim — they came from a real glm-4.7-flash matrix at the prior freeze tag (9977e85) and remain valid. Phase 8 implementation work did not retroactively invalidate them per HARNESSES_FROZEN.md tag-moves log."
  - "streaming_react block documents the Ollama exclusion narrative (08-05-VERIFY.md FAIL) and cites Ollama issue #13840 as the predicted-but-distinct failure mode."
  - "The 8 new harness blocks land between the original code-gen family and Part 1 numerical findings, with explicit signposting that no fresh numbers exist yet for the new harnesses."
  - "Article header and footer dual-cite both freeze tags so a future matrix rerun against 2af30fc produces comparable numbers without invalidating the existing 8-harness comparison."

patterns-established:
  - "Qualitative-only article refresh: when matrix rerun is gated on hardware/methodology, document the constraint honestly and ship the design-space description without fabricated numbers"
  - "Freeze-tag dual citation: prior tag = source of cited numbers, current tag = source of cited code"

requirements-completed:
  - "ART-05"

# Metrics
duration: 5min
completed: 2026-04-25
---

# Phase 8 Plan 08: Article + Medium HTML refresh (qualitative-only) Summary

**Eight Phase 8 harness description blocks landed in writeup/article.md (with Mermaid diagrams + framework mapping + freeze-SHA citations); article-medium.html regenerated with 18 PNG diagrams; the matrix rerun is gated on hardware constraints and documented honestly as "implemented but unmatrixed" rather than faked with a uniform-zero table.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-04-25T21:01:56Z
- **Completed:** 2026-04-25T21:07:19Z
- **Tasks:** 4 (8 diagrams, article body, Medium HTML regen, REQUIREMENTS update)
- **Files modified:** 19 (writeup/article.md, writeup/article-medium.html, 8 Mermaid sources, 9 new diagram PNGs, REQUIREMENTS.md, 1 PNG renamed)

## Accomplishments

- 8 per-harness description blocks added under a new top-level `## Phase 8 expansion` section, following the EXACT template the original 8 harness blocks use (what-it-does / in-production / strengths / weaknesses / use-when / Mermaid)
- Each block names the design constraint from CONTEXT.md (multi_agent's ~3× tokens, tree_of_thoughts's heuristic-vs-paper-faithful trade-off, cached_react's cell-scoped-only caveat, etc.)
- streaming_react block documents the Ollama exclusion narrative — cites 08-05-VERIFY.md FAIL outcome, cites Ollama issue #13840, and explains the OOM failure-mode-vs-#13840 distinction
- New `## Phase 8: harness expansion without matrix rerun` methodology section explains the constraint: glm-4.7-flash declares 23.4 GiB, host has 6.9 GiB free, mistral:7b smoke = 0/5 (below the tool-use floor); future practitioners with stronger hardware can rerun against freeze tag `2af30fc`
- Framework-mapping subsection cites Yao et al. 2023, Wang et al. 2022, Gao et al. 2022, CrewAI/AutoGen/LangGraph, Pydantic-style validation, streaming early-termination, in-cell memoization, loop-detection-and-recovery
- writeup/article-medium.html regenerated via scripts/build_medium_html.py: 64,414 bytes, 18 PNG diagrams referenced (was 10), all 8 new harness names appear in rendered HTML, freeze SHA `2af30fc` appears 7 times
- REQUIREMENTS.md ART-05 marked Complete

## Task Commits

Each task was committed atomically:

1. **Task 1: 8 Mermaid diagram source files** — `1d885b6` (docs)
2. **Task 2: 8 harness blocks + framework mapping + methodology note in article.md** — `92a6486` (docs)
3. **Task 3: Regenerated Medium HTML + 9 new diagram PNGs** — `7b0ddef` (docs)
4. **Task 4: ART-05 marked complete in REQUIREMENTS.md** — `4caa89e` (docs)

## Files Created/Modified

**Created (8 Mermaid source + 8 new PNGs):**
- `writeup/diagrams/{tree_of_thoughts,multi_agent,react_with_replan,self_consistency,program_aided,tool_use_with_validation,streaming_react,cached_react}.md` — Mermaid sources per harness
- `writeup/diagrams/diagram-10-ecfca6c7.png` through `diagram-17-35bd875f.png` — 8 new rendered PNGs for the new harness blocks
- `writeup/diagrams/diagram-18-00f0ae10.png` — the existing combined-lesson diagram, renumbered by mmdc's content-addressed counter

**Modified:**
- `writeup/article.md` — +264 lines: Phase 8 expansion section + framework mapping + methodology note + freeze-SHA citation updates in header byline and footer
- `writeup/article-medium.html` — regenerated, 64,414 bytes
- `.planning/REQUIREMENTS.md` — ART-05 [ ] → [x], traceability table marked Complete, coverage summary updated

**Renamed (mmdc renumbering):**
- `writeup/diagrams/diagram-10-00f0ae10.png` → `diagram-18-00f0ae10.png` (content-identical; counter shifted because 8 new diagrams were inserted ahead of it)

## Decisions Made

- **Scope pivot to qualitative-only.** The original plan assumed fresh `runs/<id>/summary.csv` from re-running both task-type matrices on the post-freeze tag. Reality: glm-4.7-flash declares 23.4 GiB system memory and the host has 6.9 GiB free; mistral:7b loaded but scored 0/5 on a 10-cell smoke (model below the tool-use floor for valid `submit_answer` payloads). A uniform-zero mistral matrix would mislead more than inform. User explicitly authorized this scope pivot.
- **Preserve 2026-04-23 numbers verbatim.** The Part 1 + Part 2 tables came from a real glm-4.7-flash matrix at freeze tag `9977e85` and remain valid for the original 8-harness comparison. Phase 8 implementation work did not touch the gated files in a way that retroactively invalidates them (per HARNESSES_FROZEN.md tag-moves log: "no matrix had been re-run against the prior tag with the **expanded** registry, so the move from `9977e85` → `2af30fc` invalidates **nothing** in the prior matrix").
- **Section placement: between code-gen family and Part 1 numerical findings.** Keeps the 8 original harness descriptions paired with their numerical results, then signposts the Phase 8 expansion as "implemented but unmatrixed," then proceeds to the existing 2026-04-23 numerical sections without disruption.
- **Header and footer dual-cite both freeze SHAs.** Header byline: "Numerical results in Part 1 and Part 2 are from glm-4.7-flash against freeze tag 9977e85 on 2026-04-23. Freeze tag has since moved to 2af30fc..." Footer: "Freeze tag at article-publish time: 9977e85 (numbers in Part 1 + Part 2 from this tag). Current freeze tag: 2af30fc (16-harness expansion; future matrix runs at this SHA produce comparable numbers for all 16 harnesses)."

## Deviations from Plan

The plan as originally written assumed fresh matrix output from both task-type matrices. The pivot to qualitative-only is the deviation, but it was authorized in the executor prompt (user explicitly stated: "the user has explicitly authorized this scope pivot"). Within the qualitative-only scope, no further deviations occurred:

- All 8 diagram source files use the exact Mermaid template style the existing 8 harness blocks use.
- All 8 harness blocks use the exact what-it-does / in-production / strengths / weaknesses / use-when / Mermaid structure of the existing blocks.
- Framework-mapping bullets cite the named papers/frameworks specified in the executor prompt verbatim.
- streaming_react block includes both the 08-05-VERIFY.md narrative AND the Ollama issue #13840 citation as required.
- The freeze SHA reference in the article footer was updated from `9977e85` to dual-cite both tags.

**One minor markdown lint warning** flagged on the new section's heading-increment: the original article already uses `### HTML-extraction family` → `#### single_shot` (h3 → h4), and my initial new section used `## Phase 8 expansion` → `#### tree_of_thoughts` (h2 → h4). Auto-fixed inline by inserting `### The 8 new harnesses` (h3) between the parent h2 and the per-harness h4 blocks, matching the original article's heading depth. No behavioral change; pure structural fix.

**Total deviations:** 1 inline auto-fix (heading-increment lint warning).
**Impact on plan:** None. All success criteria met; structure now matches existing article.

## Issues Encountered

None during execution. The mmdc renderer renumbered diagram filenames because 8 new mermaid blocks were inserted ahead of the existing combined-lesson diagram; mmdc's content-addressed counter (index + sha1[:8]) handled this cleanly — the rendered HTML references the correct new slot, and the orphaned old slot-10 file was removed in the same commit as the rename.

## Streaming_react article framing

**Implemented but unmatrixed.** The harness block in the article explicitly states: "**NOT MATRIX-VALIDATED** on the current local backend. The freeze-time verification (`08-05-VERIFY.md`) found the configured Ollama backend cannot host glm-4.7-flash on this hardware: the model declares 23.4 GiB system memory; the host has 6.9 GiB available. The failure mode differs from the predicted Ollama issue #13840 (post-tool-call generation halt) but the practical implication is identical — the harness is registered with `task_type=[]` (excluded from the local-model matrix). The implementation exists, all unit tests pass, AST seal passes; only the operational cell run is missing."

## Counts

- HTML matrix table rows: **unchanged** (5 from original Part 1; the 8 new harnesses are described qualitatively, not in the numerical table)
- Code-gen matrix table rows: **unchanged** (5 from original Part 2; same reasoning)
- New harness blocks added: **8** (tree_of_thoughts, multi_agent, react_with_replan, self_consistency, program_aided, tool_use_with_validation, streaming_react, cached_react)
- New Mermaid diagram source files: **8**
- New PNG diagrams in writeup/diagrams/: **9** (8 new harness diagrams + 1 renumbered combined-lesson diagram = 18 total references in the regenerated HTML)
- Freeze SHA `2af30fc` references in article.md: **7**
- Freeze SHA `2af30fc` references in article-medium.html: **7**

## Phase 8 closeout status

All 12 phase requirements satisfied:
- HARN-08, HARN-09, HARN-10, HARN-11, HARN-12, HARN-13, HARN-14, HARN-15 — closed in 08-02 / 08-03 / 08-04 / 08-05
- BENCH-06, RUN-07, ANAL-06 — closed in 08-06
- ART-05 — closed in this plan (08-08), qualitative-only

**Tag move:** logged in HARNESSES_FROZEN.md (08-07). Tag at `2af30fc`. Force-pushed to origin.

**Matrix re-runs:** **NOT** completed. The matrix rerun is gated on hardware (24+ GiB free system memory for glm-4.7-flash) OR a methodology shift to a different frozen model. Both are out of scope for this plan. The freeze tag at `2af30fc` is the anchor a future practitioner with sufficient hardware can rerun against.

## Self-Check: PASSED

- All 4 created files exist on disk: writeup/article.md, writeup/article-medium.html, .planning/phases/08-expand-harness-family/08-08-SUMMARY.md, .planning/REQUIREMENTS.md
- All 8 Mermaid source files exist: writeup/diagrams/{tree_of_thoughts,multi_agent,react_with_replan,self_consistency,program_aided,tool_use_with_validation,streaming_react,cached_react}.md
- All 4 task commits exist in git log: 1d885b6, 92a6486, 7b0ddef, 4caa89e
- All 18 PNG diagrams referenced in the regenerated HTML exist on disk under writeup/diagrams/
- Article header byline + footer dual-cite both freeze SHAs (9977e85 for prior numbers, 2af30fc for current code)
- streaming_react block cites Ollama issue #13840 + 08-05-VERIFY.md FAIL outcome
- ART-05 marked Complete in REQUIREMENTS.md (line 78: [x], line 184: Complete in traceability table)

## Next Phase Readiness

- Phase 8 is shippable as a qualitative-only refresh.
- The 16-harness design space is documented in writeup/article.md.
- Future plan: numerical validation of the 8 new harnesses against freeze tag `2af30fc` on hardware that can host glm-4.7-flash. Out of scope for this plan; user-gated like Phase 5.
- ROADMAP.md Phase 8 plan-progress: 8/8 plans complete with SUMMARY.

---
*Phase: 08-expand-harness-family*
*Completed: 2026-04-25*
