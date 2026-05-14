# Users and Use Cases

AdaHarness is a harness drift analyzer for LLM agent projects. It helps teams
decide whether their current planning, verification, retry, tool-control, and
autonomy settings are too heavy, too weak, or still appropriate after a change.

## Target Users

### Agent Infrastructure Engineers

They own reliability, latency, cost, model migration, and harness complexity.
AdaHarness should help them answer: which controls are useful, which are
wasteful, and which failure modes need stronger control?

### AI Platform Teams

Platform teams can run AdaHarness in CI after model, prompt, tool, or runtime
changes. The output should be a drift report and suggested policy diff, not a
new runtime dependency.

### AI Application Developers

Application teams can audit whether a cheaper model needs stronger controls or
whether a stronger model is being slowed by an old heavy harness.

## Core Use Cases

### Model Migration Drift

Compare traces before and after a model change. AdaHarness should report whether
the existing harness is over-controlling the new model or under-controlling a
weaker replacement.

### Harness Cost Audit

Find controls that add cost or latency without catching failures:

```text
Verifier catch rate: 1.8%
Verifier cost share: 29%
Recommendation: verification_control always -> selective
```

### Small Model Hardening

Detect signals that the harness is too weak:

```text
Tool result ignored in 14% of runs.
Recovery failures increased to 21%.
Recommendation: retry_control single -> bounded
```

### Regression Gate

Use AdaHarness in CI with project traces or eval results. Fail the gate only
when harness drift or underconstraint risk crosses explicit thresholds.

## Output Artifacts

| Artifact | Purpose |
| --- | --- |
| `analysis.json` | Combined machine-readable result for CI or dashboards. |
| `metrics.json` | Observable harness metrics from traces, with per-group metrics when requested. |
| `diagnosis.json` | Fit verdict plus signals with evidence, confidence, rules, and trace warnings. |
| `policy_diff.json` | Suggested changes to the current harness policy. |
| `report.md` | Human-readable explanation and next actions. |

## Non-Goals for MVP

- Do not control the user's runtime.
- Do not require users to implement AdaHarness adapter hooks.
- Do not rely on abstract model capability scores as the primary evidence.
- Do not ship a reference runtime as part of the MVP.
