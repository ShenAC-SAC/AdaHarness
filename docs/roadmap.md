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

- LLM-generated harness policies.
- Online adaptive harness changes during execution.
- Public benchmark packs and reproducible leaderboard reports.

## Backlog Candidates

These are future GitHub issue candidates when public task tracking becomes
useful. Keep them in the roadmap for now.

- `feat(runtime): define RunTrace schema`
- `feat(profiler): define capability task schema`
- `docs(research): document Minimal Effective Harness`
- `docs(project): explain why AdaHarness is not another agent framework`
