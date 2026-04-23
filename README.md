# harness_eng

**Same model, five harnesses, one benchmark.**

A controlled experiment: hold the model constant, vary the scaffolding, measure the spread in success rate and cost. The hypothesis is that harness design dominates model choice within a tier.

## The setup

- **Task**: structured field extraction from messy HTML. 40-task suite. Deterministic exact-match grader per field.
- **Model**: frozen. Default `claude-sonnet-4-6`, temperature 0, max_tokens 2048. Set once in `src/harness_eng/config.py` / `.env`. Every harness must route through `model.call()`.
- **Harnesses**:
  1. `single_shot` — entire HTML + instructions in one message, ask for JSON.
  2. `react` — thought / action / observation loop with a hard turn cap.
  3. `plan_execute` — one planning call emits a checklist, a separate executor follows it.
  4. `reflexion` — on grader failure, model critiques its own trace and retries once.
  5. `minimal` — reduced toolset (no raw HTML dump), context pruned every N turns.
- **Metrics per run**: success (0/1 per field + overall), input/output tokens, tool calls, wall-clock.
- **Traces**: every call and tool invocation is appended to `traces/{harness}/{task_id}/{run_id}.jsonl` from the first call, not retrofitted.

## Quickstart

```bash
python -m venv .venv && . .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
cp .env.example .env                           # set ANTHROPIC_API_KEY

# Sanity pilot (5 tasks x 5 harnesses). Estimate spend before running full.
python scripts/run_pilot.py

# Full run (40 tasks x 5 harnesses x N seeds)
python scripts/run_full.py --seeds 1

# Aggregate + chart
python scripts/make_chart.py
```

## Layout

```text
src/harness_eng/
  config.py         frozen model + experiment constants
  model.py          single Anthropic client wrapper all harnesses use
  trace.py          JSONL trace writer
  tools.py          shared tool schemas + dispatch
  tasks/
    loader.py       load tasks.jsonl + HTML fixtures
    tasks.jsonl     task specs (id, html_path, fields, expected)
    fixtures/       HTML files
  grader.py         exact-match field grader
  harnesses/
    base.py         abstract Harness(task) -> Result
    single_shot.py
    react.py
    plan_execute.py
    reflexion.py
    minimal.py
  runner.py         orchestrates the matrix
  analysis.py       aggregates traces -> summary + frontier chart
scripts/            thin CLI entry points
tests/              grader + loader smoke tests
```

## Controls

Things held constant across harnesses:

- Model ID, temperature, max_tokens.
- Task set and grader.
- Tool implementations (though the *subset* exposed varies per harness by design).
- System-prompt role framing (each harness owns its own *control flow* prompt but not the base role).

Things that vary by design and are the independent variable:

- Control flow (single call vs loop vs plan/execute vs retry vs pruned).
- Turn cap.
- Tools exposed.
- Context management.

## Honest scope

40 tasks is a pilot, not SWE-bench. The point is the *spread* across harnesses on the same model, not absolute rankings. Rerun with more seeds if the spread is within noise.
