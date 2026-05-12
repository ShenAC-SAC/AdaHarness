# Users and Use Cases

AdaHarness is a model-aware harness control compiler for LLM agents. It
profiles a model, generates a `HarnessPolicy`, and compiles the minimal
effective control surface for that model, task type, budget, and risk level.

The core question is not only "which model scores higher?" It is "how should
this model be constrained, released, verified, given tools, and recovered from
failure?"

## Target Users

### Agent Infrastructure Engineers

Infra engineers own agent reliability, model migration, tool integration, and
cost control. AdaHarness should help them answer how strong planning,
verification, retry, tool control, and autonomy should be. The main outputs are
`HarnessPolicy`, `HarnessSpec`, policy/controller diffs, binding reports, and
migration recommendations.

### AI Platform Teams

Platform teams support many models across shared runtimes. AdaHarness can serve
as a model onboarding and harness calibration tool: profile a new model, generate
its default policy, compile a runtime spec, and validate it against regression
tasks.

### AI Application Developers

Application teams need cost and reliability tradeoffs. AdaHarness helps compare
small model plus stronger harness against frontier model plus lighter harness,
and identifies which controls can be removed when a stronger model does not need
them.

### Model and Open Model Teams

Model teams can use AdaHarness to diagnose agentic weaknesses such as planning,
tool use, recovery, self-verification, and context discipline. The result should
inform both training priorities and recommended runtime controls.

## Core Use Cases

### Model Migration Harness Update

When moving from model A to model B, the harness may need to change. AdaHarness
should compare old and new profiles, old and recommended policies, controller
diffs, risk changes, cost changes, and the recommended migration plan.

Example recommendation:

```text
Downgrade verifier from always to selective.
Reduce retry policy from aggressive to bounded.
Increase autonomy budget from small to large.
Keep moderate tool gatekeeping.
```

### Small Model Enablement

Small, local, or cheaper models may need stronger harness support. AdaHarness
should identify the minimum control levels needed to make the model usable, such
as strict planning, summarized context, strict tool control, selective or
always-on verification, and bounded retry.

### Strong Model Deconstraint

Stronger models can be slowed or over-constrained by a harness built for weaker
models. AdaHarness should identify redundant controls, such as mandatory
planning, aggressive retries, always-on verification, or unnecessary subagent
fanout.

### Task-Specific Harness Assembly

Different task classes need different controls. Low-risk summarization may use a
light control surface. Tool-heavy workflows may need gatekeeping, recovery, and
verification. High-risk external actions may require strict verification, audit
traces, and later human approval.

### Harness Regression Test

Model upgrades should regression-test the harness, not only the model. AdaHarness
should detect when the old policy has drifted, adds cost without lift, or misses
new failure modes under the replacement model.

### Runtime-Agnostic Harness Policy

AdaHarness should export neutral `HarnessSpec` artifacts that can be mapped into
different runtimes. The project should avoid binding core controller semantics
to one agent framework.

## Output Artifacts

| Artifact | Purpose |
| --- | --- |
| `ModelProfile` | Diagnoses planning, tool use, recovery, verification, context handling, and cost sensitivity. |
| `HarnessPolicy` | States how much control, verification, retry, context management, and autonomy to apply. |
| `HarnessSpec` | Converts policy into controller levels, triggers, budgets, and runtime-facing configuration. |
| Policy and controller diff | Shows how the harness should change when model, task, risk, or budget changes. |
| Decision report | Explains the recommendation, tradeoffs, expected impact, and next actions. |

## Migration Metrics

- `harness_drift_score`: how poorly the old harness fits the new model.
- `overconstraint_penalty`: extra cost, latency, and intervention without enough
  success gain.
- `underconstraint_risk`: failure risk from running a weak model with too little
  control.
- `policy_delta`: changed policy fields, controller levels, triggers, budgets,
  and strength changes.
- `minimal_effective_harness_score`: the lightest harness that satisfies success
  and risk requirements.

## User Journeys

New model onboarding:

```bash
adaharness profile --model new-model --taskset tasks/profiler --out runs/new-profile.json
adaharness recommend --profile runs/new-profile.json --risk medium --budget standard --out runs/new-policy.json
adaharness assemble --policy runs/new-policy.json --out runs/new-harness-spec.json
adaharness report --profile runs/new-profile.json --policy runs/new-policy.json --spec runs/new-harness-spec.json
```

Model migration:

```bash
adaharness migrate \
  --from-profile runs/model-a-profile.json \
  --to-profile runs/model-b-profile.json \
  --from-policy runs/model-a-policy.json \
  --taskset tasks/production-regression \
  --out runs/migration-report.md
```

`recommend`, `assemble`, `migrate`, and `refine` are the commands that express
the product value most directly. `compare` remains the validation command behind
those decisions.
