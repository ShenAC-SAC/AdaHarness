# What AdaHarness Is Not

AdaHarness is not a replacement for LangChain, LangGraph, OpenAI Agents SDK, or
other agent runtimes.

It is an evaluation-first adaptive harness layer that can sit above different
runtimes. Its job is to profile models, select or propose harness policies, and
measure harness lift versus harness tax.

Early versions intentionally avoid:

- General multi-agent orchestration.
- Heavy benchmarks before trace-backed evaluation is stable.
- Prompt-only optimization.
- LLMs editing repository code.
- Leaderboards without reproducible traces.
