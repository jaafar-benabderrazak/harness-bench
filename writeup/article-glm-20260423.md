# Same model, five harnesses, one benchmark

*Published 2026-04-23. Run generated against freeze commit `05554d3` (`git rev-parse harnesses-frozen`), backend: Ollama `glm-4.7-flash:latest` on local inference.*

## Hook

![success rate vs wall-clock across five harnesses](frontier-glm-20260423.png)

Five agent harnesses. Same frozen model (`glm-4.7-flash:latest`, temperature 0, max_tokens 2048). One deterministic HTML-extraction benchmark. Spread in task success rate: **1.50×**. Spread in wall-clock: **8.86×**.

On an open-source model running locally, the **simplest harness tied for best success rate at one-ninth the wall-clock time of the worst.** The received wisdom is that harness investment — ReAct loops, plan-then-execute pipelines, Reflexion retries — beats naive single-shot prompting. On a weaker base model, that's actively wrong.

## Why this matters

The AI-eng discourse is model-obsessed. When a new model drops, benchmarks move. What gets undersold is that the scaffolding around the model — the harness — is a much bigger lever than most teams acknowledge. This post isolates the harness as the independent variable: freeze the model, freeze the task set, freeze the tools, and vary only the control flow around them.

The result has teeth in both directions. Harness design *does* matter. But below a base-model reliability threshold, adding turns adds failure modes faster than it adds accuracy.

## The setup

- **Task**: structured field extraction from 5 messy HTML pages (product, job post, event, recipe, paper metadata). 3–5 expected fields per task. Deterministic grader: per-field NFC + casefold + whitespace-collapse exact match.
- **Model**: `glm-4.7-flash:latest` (19 GB, Ollama local inference), temperature 0.0, max_tokens 2048. Frozen in `src/harness_eng/config.py`. Every harness routes through a single `model.call()` function; an AST-walking test enforces that only `model.py` imports the LLM SDK.
- **Harnesses** (the independent variable):
  1. **single_shot** — stuff everything into one call; `submit_answer` is the only tool.
  2. **react** — thought/action/observation loop with a 12-turn cap. Tools: `read_html`, `css_select`, `extract_text`, `submit_answer`.
  3. **plan_execute** — one planning call writes a checklist without seeing HTML, then an executor follows it. No `read_html` in the executor.
  4. **reflexion** — first attempt as ReAct; on grader failure the model critiques its own trace and retries once.
  5. **minimal** — ReAct with a deliberately reduced tool allowlist: no `read_html`, no `extract_text`, only `css_select` and `submit_answer`. Context pruned every 4 turns.
- **Metrics per cell**: task success (all fields correct), per-field accuracy, input/output tokens, tool calls, wall-clock, stop reason.
- **Methodology**: all five harnesses, `tools.py`, and `model.py` are pinned under the `harnesses-frozen` git tag. The runner's `check_freeze_gate()` pre-flight refuses to execute if any gated file has drifted — peek-and-patch is structurally prevented, not just discouraged.

## Results

| harness      | trials | successes | success rate | field accuracy | input tok | output tok | tool calls | wall-clock (s) | Wilson 95% CI |
|--------------|--------|-----------|--------------|----------------|-----------|------------|------------|----------------|---------------|
| single_shot  | 5      | 3         | 0.60         | 0.88           | 3,571     | 1,359      | 0          | 70             | 0.23 – 0.88   |
| minimal      | 5      | 3         | 0.60         | 0.72           | 22,512    | 6,049      | 98         | 306            | 0.23 – 0.88   |
| react        | 5      | 2         | 0.40         | 0.68           | 8,918     | 2,072      | 20         | 113            | 0.12 – 0.77   |
| reflexion    | 5      | 2         | 0.40         | 0.56           | 9,134     | 3,292      | 9          | 181            | 0.12 – 0.77   |
| plan_execute | 5      | 2         | 0.40         | 0.40           | 52,880    | 12,000     | 136        | 618            | 0.12 – 0.77   |

![per-task × per-harness field accuracy](field_heatmap-glm-20260423.png)

### Stop-reason distribution

| harness      | submitted | turn_cap | error |
|--------------|-----------|----------|-------|
| single_shot  | 5         | 0        | 0     |
| react        | 4         | 0        | 1     |
| plan_execute | 2         | **3**    | 0     |
| reflexion    | 3         | 0        | **2** |
| minimal      | 4         | 1        | 0     |

Two distinct failure modes that plan_execute and reflexion hit respectively: **turn-cap exhaustion** (planner produces a counterfactual plan, executor can't revise) and **malformed tool_call** (`ResponseError: mismatched arg_key and arg_value counts` from Ollama rejecting what the model emitted). Both are absent from single_shot.

## What surprised me

### 1. The simplest harness tied for best

single_shot: 3/5 success at 70 seconds. minimal: 3/5 at 306 seconds. Every "smarter" harness landed at 2/5. This is the opposite of the pre-registered hypothesis, which expected ReAct / plan_execute to lead and single_shot to land mid-pack.

What's going on: glm-4.7-flash follows a 5-field tool schema well enough on the first try — single_shot had 100% schema compliance, every cell emitted a `submit_answer` tool call with the right keys — but its multi-turn tool loops drift. Harnesses that lean on iteration inherit those drift risks without being able to convert iteration into value when the first-try signal is already clean.

This result is not "harness design doesn't matter." It's that **harness design dominates within a tier only where the base model's tool-use is reliable enough to benefit from iteration**. Below that threshold, adding turns adds failure modes faster than it adds accuracy.

### 2. plan_execute collapsed exactly the way the pitch predicted

60% turn-cap rate. The cleanest example is [`traces/plan_execute/product_01`](../traces/plan_execute/product_01/): the planner (first call, no HTML visible) produced a checklist with selectors like `h1.product-title, .product-title, h1` for title and `.product-brand, .brand, [itemprop="brand"]` for brand. The actual `product_01.html` uses `h1.title` and `<div class="brand-line">Brand: <a>Lumina</a></div>` — none of the planner's guesses match.

The executor saw the HTML, tried the planner's selectors, got NO_MATCH back, then looped through turns 2–12 retrying `.brand` / `.price` / `[itemprop="price"]` in identical batches of 3 until the turn cap fired. It never called `submit_answer`. Predicted fields: `None`.

The planner couldn't see the HTML when it wrote the plan. The executor could see the HTML but couldn't revise the plan. No backchannel = no recovery. This is "the plan is wrong from step one" made concrete.

### 3. reflexion didn't rescue failures — it added new ones

reflexion's 3 successes are all cases where the *first* attempt already succeeded; the critique-and-retry loop never turned a failure into a success in this run. Worse, on job_01 and paper_01 the first attempt hit the `mismatched arg_key` tool-call error, *and then the retry hit the same error again*. The critique call doesn't help when the failure mode is a malformed tool call at the SDK boundary rather than a reasoning error.

Net: reflexion paid 11k input / 3.3k output tokens and 181 seconds of wall-clock to recover zero tasks over react. Its value is gated on the critique catching the error — and on glm-4.7-flash, many errors are structural (Ollama rejecting the emitted tool call) rather than semantic.

### 4. minimal's structural restriction was more expensive than predicted

minimal's whole point is removing `read_html` and forcing targeted CSS-selector navigation. On glm-4.7-flash this turned into **98 tool calls across 5 cells** — the model spray-tried selectors without being able to fall back to reading raw HTML. Still reached 3/5, but at 306 seconds — 4.4× single_shot's wall-clock.

The token-budget claim survives (minimal's input-token total is 42% of plan_execute's). The time-cost claim does not. On an API backend paying per-token, minimal is a win. On local inference paying per-minute, it is not.

## Implications for harness design

Six concrete takeaways, actionable by EOD tomorrow:

1. **Match harness complexity to base-model reliability.** Before investing in a multi-turn harness, verify the model follows the tool schema cleanly on a single call. Run a 10-sample single-shot baseline on your exact tool schema; if schema adherence is below ~90%, multi-turn harnesses will underperform.

2. **The `submit_answer` universal output channel was load-bearing.** Every harness here terminates by calling the same tool — no free-form text parsing. This eliminates a whole class of "model answered in prose instead of JSON" confounds that would otherwise dominate the failure distribution on weaker models. Adopt this pattern across every harness.

3. **plan_execute needs a feedback loop between the executor and the plan.** The "plan once, execute forever" structure fails catastrophically when the plan's a-priori selectors don't match reality. Minimum viable fix: give the executor a `revise_plan` tool. Correct fix: let the planner see a sample of the HTML. The rigid split is the bug.

4. **Tool-call error handling belongs in the harness, not the SDK.** `mismatched arg_key` failures from Ollama propagated as hard run errors. A production harness would catch the malformed output, repair the tool call, and continue — the current harnesses catch nothing and simply end the run. That cost react 20% and reflexion 40% of their cells. Even a naive retry-on-malformed-tool-call loop would move the needle.

5. **minimal's structural restriction is worth it for token budgets, not for speed.** Pay-per-token backends: minimal wins. Pay-per-minute backends: it loses. Know which regime you're in.

6. **Single_shot is the honest baseline — always run it.** On this model, on this task, it beat every clever harness on the wall-clock / success frontier. If your clever harness doesn't beat single_shot, either the clever harness is wrong or the base model is too weak for cleverness to pay off. Either way you need to know before shipping.

## Honest scope

- **5 tasks × 1 seed is a pilot.** Wilson 95% CIs overlap heavily (single_shot/minimal at 3/5: `[0.23, 0.88]`; the 2/5 group: `[0.12, 0.77]`). The *ranking* between 3/5 and 2/5 is not statistically reliable at this sample size. What IS reliable: the wall-clock spread (70s to 618s is 8.9×, not a tie) and the failure-mode distribution (plan_execute's 60% turn-cap rate and reflexion's 40% tool-call error rate survive small-N noise — those are signals about the harnesses themselves, not about the specific tasks).
- **No held-out fixtures.** All 5 pages were visible during harness development. See [`HELD_OUT.md`](../HELD_OUT.md) for the explicit decision and rationale. Generalization claims are scoped to this suite; read v2 roadmap in `REQUIREMENTS.md` for the held-out path.
- **glm-4.7-flash is one open-source 19 GB model on CPU-heavy local inference.** Results will look different on Claude Sonnet / GPT-4o / Gemini 2.0 — those are the runs that could re-open whether plan_execute / reflexion beat single_shot. The harness-dominance hypothesis is about what happens *within a model tier*; this run is one tier.
- **5 tag-moves in the commit log.** Each move is documented in [`HARNESSES_FROZEN.md`](../HARNESSES_FROZEN.md) with a reason. None was post-result; every move was structural (adding tests, backend switch) and happened before the matrix was executed against the newer tag. The `runs/20260423_150654_1d6c/` directory in this article's numbers was produced against freeze commit `05554d3`.

## Reproduce

```bash
git clone https://github.com/jaafar-benabderrazak/harness_eng && cd harness_eng
pip install -e ".[dev]"
cp .env.example .env     # HARNESS_BACKEND=ollama, HARNESS_MODEL=glm-4.7-flash:latest
ollama pull glm-4.7-flash:latest
pytest -q
python scripts/run_full.py --seeds 1 --yes
python scripts/make_chart.py
```

All 47 tests offline, no API key needed. Matrix execution is local and free.

---

*Auto-generated numbers from `results/summary.csv` against run `20260423_150654_1d6c`. Narrative sections written by hand from trace evidence in `traces/`. Re-rerunning the matrix produces a new set of numbers; the narrative applies to this specific run.*
