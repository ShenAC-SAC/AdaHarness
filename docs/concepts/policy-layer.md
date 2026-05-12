# Harness Policy Layer

AdaHarness is a control plane for agent harnesses, not a replacement runtime.

It decides what controls a model should receive, compiles those controls into a
runtime-neutral spec, and later binds that spec to an existing agent runtime.
The actual agent loop, state management, streaming, tool execution, persistence,
and human approval flow stay in the user's runtime.

## Product Boundary

```text
ModelProfile -> HarnessPolicy -> HarnessSpec -> RuntimeBinding -> external runtime
```

`ModularHarness` is the reference runtime used for local validation. It proves
that a policy can enable, disable, and tune controls, but production users should
not have to rewrite their agent projects around AdaHarness modules.

## Layers

| Layer | Role |
| --- | --- |
| Core | Profile models, recommend policy, compile specs, diff policies, refine from traces. |
| Reference runtime | Validate that policies can change module behavior in AdaHarness-owned tests. |
| Adapters | Map `HarnessSpec` controls to an existing runtime's hooks, middleware, or config. |

## What Policy Controls

`HarnessPolicy` is the high-level strategy: planning depth, tool gatekeeping,
verifier strength, retry policy, autonomy budget, subagent policy, and context
policy.

It does not control an external agent by itself. It must be compiled and bound:

```text
HarnessPolicy -> compile_policy_to_spec() -> HarnessSpec -> RuntimeAdapter
```

## What Spec Controls

`HarnessSpec` is the runtime-neutral control contract. It names the controls to
enable, their configuration, and the runtime capabilities required to support
them. In the reference runtime those controls map to AdaHarness modules. In an
external runtime they must map through an adapter.

A spec should expose `source_policy`, `requirements`, and `adapter_hints` at the
top level so adapters can reject unsupported control plans before execution.

## What Adapters Control

A `RuntimeAdapter` inspects a runtime's capabilities and produces a
`RuntimeBinding` that explains how each control maps to concrete hooks such as:

- `before_model_call`
- `after_model_call`
- `before_tool_call`
- `after_tool_call`
- `before_final`
- `on_retry`
- `trace_export`

Without a binding, AdaHarness can only recommend and explain. With a binding, it
can guide how an existing agent project applies the controls.

The first adapter contract only produces a binding report. It does not mutate
LangGraph, OpenAI Agents SDK, or user-owned agent objects. Runtime-specific
automatic application can be added after the binding contract is stable.

## Non-Goals

- AdaHarness should not become a full LangGraph, OpenAI Agents SDK, or custom
  agent runtime replacement.
- Users should not need to reimplement their production harness using
  AdaHarness internal modules.
- Provider credentials and runtime wiring should come from project config, not
  repeated command-line flags.
