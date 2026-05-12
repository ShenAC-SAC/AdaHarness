# Capability Profiler

The v0.3 profiler measures agent-relevant capabilities rather than general
knowledge benchmarks. It remains deterministic for now, but tasksets already
produce diagnostic evidence for future live model runs.

## Capability Dimensions

- `planning`
- `tool_use`
- `instruction_following`
- `self_verification`
- `context_management`
- `recovery`
- `cost_sensitivity`
- `delegation`

## Profile Shape

`ModelProfile` keeps top-level scalar fields for compatibility with policy
selection and evaluation. It also includes nested `CapabilityScore` objects with
confidence, evidence, and failed cases.

Run a task-backed profile:

```bash
uv run adaharness profile --model small-sim --taskset tasks/profiler
```

The output includes `weaknesses` and `recommended_controls`, which are intended
for future harness policy generation.
