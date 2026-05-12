# Product Architecture

AdaHarness is not just a benchmark and not a general agent framework. It is a
model-aware, policy-driven modular harness compiler.

## Core Definition

```text
AdaHarness profiles a model and compiles a HarnessPolicy into a modular agent harness.
```

The core flow is:

```text
ModelProfile -> HarnessPolicy -> HarnessSpec -> ModularHarness -> RunTrace -> PolicyRefinement
```

The product thesis is:

```text
When you change the model, you may need to change the harness. AdaHarness tells you how.
```

## Core Objects

| Object | Purpose |
| --- | --- |
| `ModelProfile` | Describes model capabilities such as planning, tool use, recovery, and self-verification. |
| `HarnessPolicy` | Human- and machine-readable strategy for how much orchestration to apply. |
| `HarnessSpec` | Runtime-facing module configuration compiled from policy. |
| `ModularHarness` | Executable harness assembled from enabled modules. |
| `RunTrace` | Evidence trail used for scoring, reporting, and policy refinement. |

## Product Modes

| Mode | Command | Purpose |
| --- | --- | --- |
| Evaluate | `compare` | Compare model x harness behavior. |
| Recommend | `recommend` | Generate the minimal effective `HarnessPolicy`. |
| Assemble | `assemble` | Compile policy into `HarnessSpec`. |
| Run | `run` | Execute a task with an assembled harness. |
| Refine | future `refine` | Propose policy updates from traces. |
| Migrate | future `migrate` | Compare old and new model policies and produce a harness migration plan. |

## Layer Boundaries

- `profiler/` produces capability evidence.
- `policies/` produces high-level strategy.
- `specs/` compiles strategy into module configuration.
- `modules/` implements individual harness controls.
- `harnesses/` assembles modules into executable harnesses.
- `runtime/` owns execution state, budget, and traces.
- `evals/` validates policies and harness behavior.

## Artifacts

Users should receive four primary artifacts:

```text
profile.json       model capability diagnosis
policy.json        executable harness strategy
harness_spec.json  assembled module configuration
report.md          human explanation and evidence
```

`compare` output is supporting evidence. The durable output is the policy and
compiled harness spec.

See `docs/use-cases.md` for target users, model migration scenarios, output
artifacts, and migration metrics.
