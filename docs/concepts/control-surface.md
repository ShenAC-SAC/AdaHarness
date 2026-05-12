# Harness Control Surface

This document describes an experimental future control layer. The current MVP is
trace-first diagnosis and suggested policy diffs; it does not require users to
adopt controller specs or runtime bindings.

AdaHarness should not treat a harness as a set of binary module switches. Its
core artifact is a control surface: a parameterized plan for how strongly an
agent runtime should plan, verify, retry, manage tools, manage context, and
limit autonomy.

The main flow is:

```text
ModelProfile + TaskProfile + Risk + Budget
  -> HarnessControlPolicy
  -> HarnessControlSpec
  -> RuntimeBinding
```

`HarnessPolicy` can keep the current compact fields for user-facing presets, but
`HarnessSpec` should expose controller-level intent. Modules remain the
reference runtime's implementation detail.

## Controllers

| Controller | Control Question |
| --- | --- |
| `planner` | How much planning should happen before or during execution? |
| `verifier` | Which outputs or checkpoints require validation? |
| `retry` | Which failures should retry, how often, and with what escalation? |
| `tool_control` | Which tool calls should be checked before and after execution? |
| `context` | Should context stay raw, be summarized, or be selected? |
| `budget` | What step, retry, tool-call, and token limits apply? |
| `delegation` | Can subagents be used, and under what conditions? |
| `autonomy` | How many consecutive model-led steps are allowed? |

Each controller should carry more than `enabled: true`:

```json
{
  "level": "conditional",
  "mode": "model_led",
  "triggers": ["task_complexity_at_least_medium"],
  "budget": {"max_plan_steps": 4, "max_replans": 1},
  "escalation": {"on_repeated_failure": "strict"}
}
```

## Planning Levels

Planning should be a graded control, not an on/off feature:

| Level | Runtime Meaning |
| --- | --- |
| `off` | No planning intervention. |
| `hint` | Prompt-level hint to plan only when useful. |
| `light` | Ask for a short checklist on complex tasks. |
| `conditional` | Require planning only when task complexity, risk, or failures justify it. |
| `explicit` | Require a plan before execution. |
| `strict` | Validate the plan, bind execution to steps, and replan on failure. |
| `externalized` | Use an external planner or split the task into delegated substeps. |

Medium planning ability usually compiles to `conditional` or `explicit`, not to
a simple module switch.

## Verification and Retry

Verification and retry follow the same pattern:

```text
verifier: off -> final_only -> selective -> always -> external
retry: none -> single -> bounded -> aggressive -> escalating
```

A strong model may use `final_only` verification and `single` retry. A weak or
high-risk profile may need selective or always-on verification plus bounded or
escalating retry.

## Contract Boundary

The controller spec is the semantic contract. A runtime adapter maps controllers
to hooks such as `before_model_call`, `after_tool_call`, `before_final`, and
`on_failure`. The reference runtime maps controllers to AdaHarness modules only
to validate behavior locally.

This may become useful after the trace-first analyzer proves that its
recommendations are trustworthy.
