# Roadmap

AdaHarness is now centered on:

```text
ModelProfile -> HarnessPolicy -> HarnessSpec -> RuntimeBinding -> external runtime
```

The standalone CLI remains the lab environment:

```text
profile -> recommend -> assemble -> run -> trace -> refine
```

`ModularHarness` remains a reference runtime for validation, not the product
boundary.

## Completed Foundation

- Reusable `HarnessPolicy` recommendation artifacts with risk and budget inputs.
- `HarnessPolicy -> HarnessSpec` compilation.
- Reference `ModuleRegistry`, `HarnessBuilder`, and `ModularHarness`.
- Policy-driven reference runtime hooks and online retry adaptation.
- Migration reports with policy diff, module diff, and drift metrics.
- Trace-backed offline refinement.
- Generic external trace normalization.

## Phase 1 Public Core API

Goal: let external projects import AdaHarness without shelling out to the CLI.

- Add stable functions for loading profiles, recommending policies, compiling
  specs, loading/saving artifacts, and building the reference harness.
- Keep CLI as a wrapper over the same API.
- Document embedded-library usage.

Acceptance: an external Python file can import AdaHarness and produce
`HarnessPolicy` and `HarnessSpec` without invoking `adaharness`.

## Phase 2 Runtime Adapter Contract

Goal: make external runtime integration explicit.

- Add `RuntimeAdapter`, `AdapterCapabilities`, and `RuntimeBinding`.
- Add a generic binding adapter that maps `HarnessSpec` controls to required
  hooks and reports unsupported controls.
- Do not mutate LangGraph/OpenAI Agents SDK objects yet.

Acceptance: `bind(spec)` produces a machine-readable binding report explaining
which hooks a target runtime must expose.

## Phase 3 HarnessSpec Contract Upgrade

Goal: make `HarnessSpec` a cross-runtime control contract, not only an internal
module list.

- Add `requirements`, `adapter_hints`, and top-level `source_policy`.
- Add helpers such as `get_module()` and requirement checks.
- Preserve backward-compatible loading for existing specs.

Acceptance: adapters can inspect a spec and decide whether a runtime supports
it before execution.

## Phase 4 Project Configuration

Goal: remove repeated provider and credential wiring from CLI arguments.

- Add `.env` loading for secrets.
- Add `adaharness.toml` for providers, models, defaults, tasksets, and runtime
  preferences.
- Add `config inspect` and `config validate`.

Acceptance: `adaharness profile --config adaharness.toml --model qwen-local`
resolves provider, base URL, taskset, risk, and budget.

## Phase 5 Live Profiling

Goal: make model profiles come from real model runs when explicitly requested.

- Keep default profiling synthetic.
- Add `profile --live` that builds a `ModelClient`.
- Score profiler task traces deterministically.
- Never call a real provider without `--live`.

Acceptance: `profile --live --provider mock` exercises the live path in CI, and
real providers require explicit configuration.

## Phase 6 Reference Runtime Behavior

Goal: make the reference runtime useful as a validation lab.

- Make planner alter messages.
- Add deterministic fake tools.
- Make verifier use task checks and traces.
- Enforce budget limits.
- Make retry and recovery change the next attempt.

Acceptance: reference traces show behavioral differences beyond trace markers.
