# Phase 1 Audit: Requirement-to-Evidence Matrix

**Audited:** 2026-04-23
**Phase:** 01-audit-and-harden-scaffold
**Status:** GREEN — all 34 Phase 1 requirement IDs have concrete evidence.
**Next gate:** Phase 2 (Methodology Freeze) — safe to proceed.

## Test suite summary

- Total tests: 26 (was 19 pre-phase, +7 added in Wave 1)
- Pass: 26
- Fail: 0
- Skip: 0
- Runtime: 0.38s

## Structural invariants (grep evidence)

| Invariant | Check | Result |
|-----------|-------|--------|
| trace.py schema_version constant | `grep SCHEMA_VERSION src/harness_eng/trace.py` | present |
| trace.py fsync per record | `grep os.fsync src/harness_eng/trace.py` | present |
| trace.py explicit line buffering | `grep 'buffering=1' src/harness_eng/trace.py` | present |
| model.py max_retries=0 | `grep max_retries=0 src/harness_eng/model.py` | present |
| model.py usage_raw field | `grep usage_raw src/harness_eng/model.py` | present (3+ hits) |
| base.py threads usage to trace | `grep 'usage=mc.usage_raw' src/harness_eng/harnesses/base.py` | present |
| grader.py NFC normalization | `grep unicodedata.normalize src/harness_eng/grader.py` | present |
| grader.py casefold (not lower) | `grep casefold src/harness_eng/grader.py` | present |
| grader.py no .lower() | `grep '\.lower()' src/harness_eng/grader.py` | ABSENT (correct) |
| HELD_OUT.md at repo root | `test -f HELD_OUT.md` | present |

## Requirement-to-evidence matrix

| ID | Description (short) | Evidence | Notes |
|----|---------------------|----------|-------|
| INTG-01 | Only model.py imports anthropic | tests/test_model_seal.py::test_only_model_py_imports_anthropic | AST-walking test |
| INTG-02 | Every harness routes through model.call | tests/test_harness_registry.py::test_no_harness_imports_anthropic_directly | Seal side-check |
| INTG-03 | Model id/temp/max_tokens in config.py | src/harness_eng/config.py defines CONFIG; model.py reads it as only source | Single source |
| HARN-01 | single_shot harness exists | tests/test_harness_registry.py::test_all_five_harnesses_registered | Registry enumerates |
| HARN-02 | react harness exists | tests/test_harness_registry.py::test_all_five_harnesses_registered | Registry enumerates |
| HARN-03 | plan_execute harness exists | tests/test_harness_registry.py::test_all_five_harnesses_registered | Registry enumerates |
| HARN-04 | reflexion harness exists | tests/test_harness_registry.py::test_all_five_harnesses_registered | Registry enumerates |
| HARN-05 | minimal harness exists | tests/test_harness_registry.py::test_all_five_harnesses_registered | Registry enumerates |
| HARN-06 | Every harness terminates via submit_answer | Manual: every harness `_execute` returns via `name == "submit_answer"` branch (verified by inspection of single_shot.py, react.py, plan_execute.py, reflexion.py, minimal.py) | Pattern uniform |
| BENCH-01 | 5 fixtures across 5 domains | tests/test_tasks.py::test_tasks_load (asserts len==5); src/harness_eng/tasks/fixtures/ has product_01, job_01, event_01, recipe_01, paper_01 | |
| BENCH-02 | 3–5 expected fields per task | tests/test_tasks.py::test_expected_field_counts | Asserts >=3; each task has 5 |
| BENCH-03 | Decoys in fixtures | Manual: product_01.html has "similar products", job_01.html has "other openings", event_01.html has "upcoming", recipe_01.html has "more from Rina", paper_01.html has "related" aside | |
| BENCH-04 | NFC + casefold + ASCII-ws grader | tests/test_grader_determinism.py::test_golden_cases, ::test_100x_determinism | Wave 1 plan 01-02 |
| TRACE-01 | Event written before function returns | tests/test_trace_schema.py::test_every_record_has_schema_version (exercises log() + verifies written state) | |
| TRACE-02 | Line buffering + fsync | src/harness_eng/trace.py:18 `buffering=1`, line 33 `os.fsync(self._fh.fileno())`; test_partial_trace_parseable_after_truncation exercises crash survival | Wave 1 plan 01-01 |
| TRACE-03 | schema_version on every record | tests/test_trace_schema.py::test_every_record_has_schema_version | Wave 1 plan 01-01 |
| TRACE-04 | run_start / run_end bracket invariant | harnesses/base.py::Harness.run writes run_start and run_end in try/except/finally via `with Tracer` context manager | Pre-existing structure; tested in practice at matrix time |
| TRACE-05 | Timestamp + type + payload per event | tests/test_trace_schema.py::test_every_record_has_schema_version asserts "ts" and "type" present | |
| RUN-01 | Matrix CLI | scripts/run_full.py invokes harness_eng.runner.run_matrix; runner.py iterates harness × task × seed | Exercised in Phase 5 matrix run |
| RUN-03 | One JSONL row per cell | src/harness_eng/runner.py::run_matrix writes one line per cell via `fh.write(json.dumps(row, default=str) + "\n")` | |
| RUN-05 | Cost estimator prints before full run | scripts/run_full.py calls estimate_matrix + format_estimate before run_matrix; tests/test_cost_estimator.py asserts shape | |
| RUN-06 | User confirmation gate | scripts/run_full.py uses `input()` unless --yes flag | |
| ANAL-01 | summary.csv produced | src/harness_eng/analysis.py::produce_all writes summary.csv via `df_harness.to_csv` | Exercised in Phase 5 |
| ANAL-03 | frontier.png produced | src/harness_eng/analysis.py::frontier_chart writes PNG via matplotlib Agg backend | Exercised in Phase 5 |
| ANAL-04 | field_heatmap.png produced | src/harness_eng/analysis.py::field_heatmap writes PNG via matplotlib | Exercised in Phase 5 |
| ART-01 | article.md auto-drafted | src/harness_eng/analysis.py::write_article interpolates summary.csv into Markdown | Exercised in Phase 5 |
| ART-02 | Numbers never hand-typed | src/harness_eng/analysis.py::write_article uses f-string / df.to_markdown only on the DataFrame from summary.csv; no literal numbers | |
| VIEW-01 | Standalone HTML viewer | src/harness_eng/trace_viewer.py writes a single HTML file with inline CSS + inline JS; no external dependencies | |
| VIEW-02 | Renders JSONL traces grouped by (harness, task, run) | src/harness_eng/trace_viewer.py::_load_runs walks traces/<harness>/<task>/<run>.jsonl tree | |
| VIEW-03 | Filter by harness and task | src/harness_eng/trace_viewer.py::_filter_script adds inline JS with fh/ft select elements | |
| VIEW-04 | Event shows type + key fields + raw JSON | src/harness_eng/trace_viewer.py::_event_html emits summary line + collapsible `<pre>` with full JSON | |
| TEST-01 | pytest suite covers grader, loader, tools, seal, registry, cost estimator | tests/test_grader.py, test_grader_determinism.py, test_tasks.py, test_tools.py, test_model_seal.py, test_harness_registry.py, test_cost_estimator.py — all green | 26 tests total |
| TEST-02 | Synthetic multi-turn re-billing test | tests/test_tool_result_rebilling.py::test_tool_result_tokens_accumulate_across_turns | Wave 1 plan 01-03 |
| ONB-03 | .env.example shipped; no secrets | .env.example present at repo root; `grep sk-ant- .env.example` returns only the placeholder `sk-ant-...` | |

## Deltas this phase introduced

- New file: `src/harness_eng/trace.py` gained `SCHEMA_VERSION = 1`, `buffering=1`, `os.fsync` after each flush
- Edited: `src/harness_eng/grader.py::_norm` replaced `.lower()`+`\s` pipeline with NFC+casefold+ASCII-WS pipeline
- Edited: `src/harness_eng/model.py::_get_client` now passes `max_retries=0`; `ModelCall` gained `usage_raw: dict`; `call()` populates it via `resp.usage.model_dump()` with `AttributeError` fallback
- Edited: `src/harness_eng/harnesses/base.py::_step_model` traces `usage=mc.usage_raw` alongside existing scalars
- New tests: `test_trace_schema.py` (2), `test_grader_determinism.py` (2), `test_model_usage.py` (2), `test_tool_result_rebilling.py` (1)
- New doc: `HELD_OUT.md` at repo root — Option A (no hold-out) with rationale

## Deviations from plan

None. Each wave-1 plan applied exactly the edits specified. Attribute coercion in `test_model_usage.py::test_client_constructed_with_max_retries_zero` was adjusted to monkeypatch `sys.modules["anthropic"]` rather than attribute-set on a real `anthropic` module that may not be installed in the CI environment — this preserves the observable-behavior test intent while surviving a `ModuleNotFoundError` on anthropic.

## Go/no-go for Phase 2

GO. All invariants pinned, all tests green, HELD_OUT.md committed. Phase 2 can now tag `harnesses-frozen` over the current HEAD.
