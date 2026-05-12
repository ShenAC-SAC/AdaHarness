# ADR 0001: Keep Provider SDKs Behind ModelClient

## Status

Accepted

## Context

AdaHarness needs to compare harness behavior across models and providers. If
OpenAI, Anthropic, or local HTTP details leak into profilers, policies, or
harness runtimes, the project will become hard to test and each new provider
will create cross-module churn.

## Decision

Define `ModelClient` in `adaharness.models.base` as the stable boundary for
model completion. Provider adapters return a shared `ModelResponse` with text,
raw provider data, and optional token usage. Provider SDKs are optional
dependencies and are imported only when their adapter is instantiated.

Prefer protocol-level adapters over brand-level adapters. DeepSeek, Qwen,
OpenRouter, vLLM, LM Studio, and similar endpoints should use the
`openai-compatible` boundary when they expose that API shape. Add a native
adapter only when the protocol is meaningfully different.

The profiler may accept `ModelConfig`, but v0.2 keeps profiling deterministic.
Task-backed profiling will call `ModelClient` in v0.3.

## Consequences

- Core tests and CLI smoke tests do not require provider credentials.
- Provider-specific failures stay isolated to `adaharness.models`.
- Future harness runtimes can operate against one protocol.
- Adapter implementations need thin translation layers for provider-specific
  message, tool, and usage formats.
