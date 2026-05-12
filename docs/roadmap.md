# Roadmap

AdaHarness should advance from deterministic harness selection toward adaptive
harness evolution while keeping each stage independently useful and testable.

## v0.1 Stabilized MVP

- Keep synthetic profiling.
- Ensure install, tests, lint, CLI comparison, and Markdown reports work.
- Document architecture, metrics, roadmap, and contribution flow.

## v0.2 Real Model Adapters

- Introduce a stable `ModelClient` protocol.
- Add OpenAI-compatible, Anthropic-compatible, and local HTTP adapter paths.
- Treat DeepSeek, Qwen, OpenRouter, vLLM, and LM Studio as protocol-level
  support targets where possible, not separate brand adapters.
- Keep provider dependencies optional.

## v0.3 Capability Profiler

- Replace synthetic-only scores with task-backed capability evidence.
- Track score, confidence, evidence, and failed cases per capability.
- Expand profiler task packs around agent-relevant skills.

## v0.4 Real Harness Runtime

- Convert static harness presets into executable runtime loops.
- Add bounded tool use, retries, verification, and budget enforcement.
- Emit structured traces for each run.

## Later Research Tracks

- LLM-generated harness policies validated as structured proposals.
- Online adaptive harness changes recorded as trace-backed policy changes.
- Public benchmark packs and reproducible `model x harness` leaderboard reports.

## Backlog Candidates

Future GitHub issues should be created here only when public task tracking
becomes useful.
