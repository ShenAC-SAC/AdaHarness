# Roadmap

AdaHarness is moving from synthetic harness comparison toward a policy-driven
modular harness system. The main product path is:

```text
profile -> recommend -> assemble -> run -> trace -> refine
```

`compare` remains important, but its role is to validate policy and harness
choices, not to be the final product output.

## v0.2 Policy as Primary Artifact

Goal: make `HarnessPolicy` the main machine-readable output.

- Keep `ModelProfile` as the diagnostic input.
- Make `recommend --out` write a reusable `policy.json`.
- Include risk and budget inputs in recommendation.
- Keep reports as explanation, not a substitute for policy.

Acceptance: `adaharness recommend --profile runs/profile.json --out runs/policy.json`
produces a policy that later commands can consume.

## v0.3 HarnessSpec Compiler

Goal: compile `HarnessPolicy` into runtime module configuration.

- Add `ModuleSpec`.
- Add `HarnessSpec`.
- Add `compile_policy_to_spec()`.
- Add `assemble --policy ... --out ...`.
- Output enabled and disabled modules.

Acceptance: `adaharness assemble --policy runs/policy.json --out runs/harness-spec.json`
produces a concrete module spec.

## v0.4 Module Registry and Harness Builder

Goal: build a runtime harness from `HarnessSpec`.

- Add `modules/` with planner, verifier, retry controller, context manager,
  budget guard, tool gatekeeper, tool executor, and trace modules.
- Add a module registry.
- Add a `ModularHarness` builder.
- Keep `TraceModule`, `BudgetGuardModule`, and `ToolExecutorModule` as core
  modules.

Acceptance: `adaharness run --harness-spec runs/harness-spec.json --task ...`
records which modules were enabled.

## v0.5 Policy-Driven Runtime Behavior

Goal: different policies create different runtime behavior, not just different
metadata.

- Planner module creates planning events.
- Verifier module checks before final output.
- Retry controller retries on verification or tool failure.
- Tool gatekeeper checks tool calls before execution.
- Budget guard limits steps, tool calls, and token use.

Acceptance: bare and strong specs produce visibly different traces on the same
task.

## v0.6 Profiler-Driven Policy Generation

Goal: generate different policies for different model profiles.

- Weak models receive stronger planner, verifier, retry, and gatekeeping modules.
- Strong models receive lighter guardrails.
- Risk and budget affect verifier strength, retry depth, and autonomy budget.

Acceptance: weak and strong profiles produce different policy JSON and different
harness specs.

## v0.7 Trace-Backed Policy Refinement

Goal: use completed runs to propose improved policies offline.

```text
run with policy -> collect trace -> analyze failure modes -> propose policy -> assemble spec
```

This is still offline adaptation, not online mutation during a run.

## v0.8 External Trace Import

Goal: evaluate external agent runtimes without executing them directly.

- Add `ExternalTraceAdapter`.
- Normalize external traces to `RunTrace`.
- Score imported traces and generate harness recommendations.

Non-goal: direct LangGraph, OpenAI Agents SDK, or Claude Agent SDK execution.

## v0.9 Online Adaptive Modules

Goal: update active modules during runtime.

- Verification failures can strengthen verifier modules.
- Tool failures can tighten tool gatekeeping.
- Budget pressure can reduce planning depth.
- Stable execution can expand autonomy budget.

Acceptance: `policy_change` events affect subsequent runtime events, not only
post-run reporting.
