# Positioning

AdaHarness is not a replacement for LangChain, LangGraph, OpenAI Agents SDK, or
other agent runtimes.

It is a model-aware harness compiler that can sit above different runtimes. Its
job is to profile models, generate `HarnessPolicy`, compile policy into
`HarnessSpec`, and explain when model, task, budget, or risk changes require the
harness to change.

The short form:

```text
When you change the model, you may need to change the harness. AdaHarness tells you how.
```

Early versions intentionally avoid:

- General multi-agent orchestration.
- Heavy benchmarks before trace-backed evaluation is stable.
- Prompt-only optimization.
- LLMs editing repository code.
- Leaderboards without reproducible traces.
