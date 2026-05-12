# Roadmap

AdaHarness is now centered on:

```text
ModelProfile + TaskProfile + Risk + Budget
  -> HarnessControlPolicy
  -> HarnessControlSpec
  -> RuntimeBinding
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
- Migration reports with policy diffs, controller diffs, and drift metrics.
- Trace-backed offline refinement.
- Generic external trace normalization.
- Public API, project config, adapter capabilities, and runtime binding reports.

## Phase 1 Harness Control Surface

Goal: make the controller model explicit so AdaHarness is not just a module
on/off assembler.

- Define planning, verification, retry, tool, context, budget, delegation, and
  autonomy controllers.
- Document levels, triggers, authority, budgets, and escalation.
- Keep modules as reference-runtime implementation details.

Acceptance: docs and specs describe controller levels rather than only runtime
module membership.

## Phase 2 Controller Specs

Goal: upgrade `HarnessSpec` to expose controller specs while keeping module
compatibility.

- Add `ControllerSpec` and `controllers` to `HarnessSpec`.
- Derive module specs from controller specs for the reference runtime.
- Preserve current JSON fields for backward compatibility.

Acceptance: `assemble` emits controller specs and existing module-based tests
still pass.

## Phase 3 Controller Binding

Goal: make adapter output explain controller-to-hook mappings.

- Bind `planner`, `verifier`, `retry`, `tool_control`, `context`, `budget`,
  `delegation`, and `autonomy` to required hooks.
- Report unsupported controllers and unsupported legacy modules separately.
- Keep the first adapter as a report-only contract.

Acceptance: `bind(spec)` produces `bindings` keyed by controller, including
hook, level, mode, triggers, and config.

## Phase 4 Live Profiling

Goal: make model profiles come from real model runs when explicitly requested.

- Keep default profiling synthetic.
- Add `profile --live` that builds a `ModelClient`.
- Score profiler task traces deterministically.
- Never call a real provider without `--live`.

Acceptance: `profile --live --provider mock` exercises the live path in CI, and
real providers require explicit configuration.

## Phase 5 Reference Runtime Behavior

Goal: make the reference runtime useful as a validation lab.

- Implement graded planner behavior first: `hint`, `light`, `conditional`,
  `explicit`, and `strict`.
- Then implement verifier and retry levels.
- Add deterministic fake tools and task-backed verification.

Acceptance: reference traces show behavioral differences beyond trace markers.
