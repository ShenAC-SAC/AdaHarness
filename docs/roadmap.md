# Roadmap

AdaHarness is now centered on:

```text
ProjectAgentAdapter -> ProjectRunTrace -> AgentSystemProfile
  -> HarnessControlPolicy
  -> HarnessControlSpec
  -> RuntimeBinding
  -> ProjectRuntimeHooks
```

The CLI should be project-local first:

```text
calibrate -> recommend -> compile -> bind -> validate -> report
```

Standalone reference commands remain a lab environment for AdaHarness
development and smoke tests. `ModularHarness` remains a reference runtime for
validation, not the product boundary.

## Completed Foundation

- Reusable `HarnessPolicy` recommendation artifacts with risk and budget inputs.
- `HarnessPolicy -> HarnessSpec` compilation.
- Reference `ModuleRegistry`, `HarnessBuilder`, and `ModularHarness`.
- Policy-driven reference runtime hooks and online retry adaptation.
- Migration reports with policy diffs, controller diffs, and drift metrics.
- Trace-backed offline refinement.
- Generic external trace normalization.
- Public API, project config, adapter capabilities, and runtime binding reports.

## Phase 1 Project-Embedded Positioning

Goal: make the product story project-local rather than standalone benchmark
first.

- Update README and docs so the main path starts inside an existing agent
  project.
- Move reference runtime and mock task flows to lab/development status.
- Explain that the host project owns model configuration, prompts, tools, and
  runtime state.

Acceptance: new users see AdaHarness as project calibration and control binding,
not a standalone model benchmark.

## Phase 2 Project Agent Adapter

Goal: define how AdaHarness evaluates a host agent project.

- Add `ProjectAgentAdapter`, `ProjectRunResult`, and `CalibrationResult`.
- Let adapters report runtime capabilities, run project tasks, and export
  traces.
- Keep the first adapter contract simple and synchronous.

Acceptance: a small custom adapter can run a task and produce traces without
reconfiguring model credentials in AdaHarness.

## Phase 3 Agent System Profile

Goal: derive policy from project evidence, not only standalone model scores.

- Add `AgentSystemProfile` as a composed profile over model signals, runtime
  capabilities, task profile, trace evidence, and failure modes.
- Add trace-backed conversion from project runs to profile signals.
- Keep `ModelProfile` as the current compatibility input.

Acceptance: `calibrate_project(...)` can recommend a policy from project task
results and runtime capabilities.

## Phase 4 Project-Local CLI

Goal: make CLI useful after AdaHarness is installed in a host project.

- Add `calibrate`, `validate`, and `bind` commands around project config.
- Treat existing `profile`, `compare`, and reference `run` flows as lab commands
  or compatibility commands.
- Avoid duplicating provider credentials when an adapter owns model access.

Acceptance: users can run `adaharness calibrate --config adaharness.toml` inside
their agent repo and receive profile, policy, spec, binding, trace, and report
artifacts.

## Phase 5 Reference Runtime Behavior

Goal: make the reference runtime useful as a validation lab.

- Implement graded planner behavior first: `hint`, `light`, `conditional`,
  `explicit`, and `strict`.
- Then implement verifier and retry levels.
- Add deterministic fake tools and task-backed verification.

Acceptance: reference traces show behavioral differences beyond trace markers.
