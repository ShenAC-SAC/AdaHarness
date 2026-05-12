# Harness Policy Layer

AdaHarness is a control plane for agent harnesses, not a replacement runtime.

It decides how much control an agent project should receive, compiles that
control surface into a runtime-neutral spec, and later binds that spec to an
existing agent runtime. The actual agent loop, state management, streaming, tool
execution, persistence, provider configuration, and human approval flow stay in
the user's runtime.

## Product Boundary

```text
ProjectRunTrace -> AgentSystemProfile -> HarnessPolicy -> HarnessSpec -> RuntimeBinding
```

`ModularHarness` is the reference runtime used for local validation. It proves
that a policy can tune controller behavior, but production users should not have
to rewrite their agent projects around AdaHarness modules.

## Layers

| Layer | Role |
| --- | --- |
| Core | Calibrate from project evidence, recommend policy, compile specs, diff policies, refine from traces. |
| Reference runtime | Validate that policies can change module behavior in AdaHarness-owned tests. |
| Adapters | Map `HarnessSpec` controls to an existing runtime's hooks, middleware, or config. |

## What Policy Controls

`HarnessPolicy` is the high-level strategy: planning depth, tool gatekeeping,
verifier strength, retry policy, autonomy budget, subagent policy, and context
policy. It should be interpreted as control strength, not as a simple list of
modules to enable.

It does not control an external agent by itself. It must be compiled and bound:

```text
HarnessPolicy -> compile_policy_to_spec() -> HarnessSpec -> RuntimeAdapter
```

## What Spec Controls

`HarnessSpec` is the runtime-neutral control contract. It names controller
levels, triggers, budgets, and escalation rules, plus the runtime capabilities
required to support them. In the reference runtime those controls map to
AdaHarness modules. In an external runtime they must map through an adapter.

A spec should expose `source_policy`, `requirements`, and `adapter_hints` at the
top level so adapters can reject unsupported control plans before execution.

## What Adapters Control

A `RuntimeAdapter` inspects a runtime's capabilities and produces a
`RuntimeBinding` that explains how each controller maps to concrete hooks such
as:

- `before_model_call`
- `after_model_call`
- `before_tool_call`
- `after_tool_call`
- `before_final`
- `on_retry`
- `trace_export`

Without a binding, AdaHarness can only recommend and explain. With a binding, it
can guide how an existing agent project applies the controls.

The binding is keyed by controller, not by AdaHarness internal module. For
example, `planner` maps to a hook plus level, mode, authority, triggers, budget,
and escalation settings. Legacy module names may appear only as compatibility
metadata for the reference runtime.

The first adapter contract only produces a binding report. It does not mutate
LangGraph, OpenAI Agents SDK, or user-owned agent objects. Runtime-specific
automatic application can be added after the binding contract is stable.

## Non-Goals

- AdaHarness should not become a full LangGraph, OpenAI Agents SDK, or custom
  agent runtime replacement.
- Users should not need to reimplement their production harness using
  AdaHarness internal modules.
- Provider credentials and runtime wiring should stay in the host agent project
  when AdaHarness is used as an embedded policy layer.
