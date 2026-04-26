<!--
LinkedIn FEED POST, short-form social. Paste body below into the LinkedIn
"Start a post" composer. Upload writeup/thumbnail.png separately when
LinkedIn shows the image picker. ~1,800 chars; under the 3,000 hard limit.

Long-form companion (LinkedIn Pulse / Medium import): writeup/linkedin-article.md
-->

Why your eval harness needs a single-shot baseline

Most teams building LLM apps reach for an agent framework first. I built a benchmark that pits a 15-line single-shot script against the default control flow of LangChain, LangGraph, CrewAI, and several other agent patterns. The script kept winning.

Starting with a baseline isn't best-practice ceremony. It's the cheapest way to find out whether your fancy framework is buying anything.

The setup

Each harness in the benchmark is a clean from-scratch implementation of the control-flow pattern a popular framework ships by default: ReAct (LangChain's AgentExecutor), plan-and-execute (LangGraph), multi-agent with isolated histories (CrewAI / AutoGen), self-critique (Reflexion paper), plus single-shot, chain-of-thought, test-driven, and retry-on-fail. Holding the model and the tasks fixed, the question is whether the control flow itself moves the numbers.

The numbers

• Accuracy on messy HTML extraction: the single-shot baseline scored 9/15. The standard ReAct loop scored 2/15.

• Speed: the baseline ran about 4x faster on wall-clock.

• Cost: at frontier-model list prices, the baseline cost roughly 1/10th per task compared to the elaborate agent loops.

Three things I didn't expect

• Hallucination at scale. A plan-and-execute agent fired the same non-existent CSS selector 417 times in a single run. The planner invented the selector. The executor had no way to tell the planner it didn't exist.

• Variance even at temperature 0. Two runs of the same matrix produced middle-of-the-pack rankings that swung by 0.33 between the runs. seeds=1 evals are a coin flip.

• On easy tasks the spread is all cost. For textbook algorithms with deterministic graders, every harness hit 15/15. The only differentiator was the bill: some test-driven patterns used 6x the input tokens to reach the same answer.

What to do with this

• Make single_shot row zero of your eval table. 15 lines of code.

• Beat the baseline by 10% or simplify. If your production agent doesn't, latency and cost both drop when you rip it out.

• Know when complexity actually pays. Only when first-shot accuracy is below target AND the failures are recoverable through extra turns. Both rarely hold at once on weak models.

None of this is anti-agent. It's pro-measurement: complexity should buy you something, and right now most of it isn't.

Full breakdown with charts and methodology:
🔗 https://jaafarbenabderrazak.com/blog/agent-frameworks-benchmark

Source code and reproducible 150-run matrix:
🔗 https://github.com/jaafar-benabderrazak/harness-bench

What's the simplest baseline you've never bothered to measure?

#SoftwareEngineering #LLMOps #AIArchitecture #AIBenchmarking #AgenticWorkflows
