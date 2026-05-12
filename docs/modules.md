# Harness Modules

AdaHarness will assemble harnesses from small runtime modules. Core modules are
always enabled; optional modules are selected by `HarnessPolicy` and compiled
into `HarnessSpec`.

## Core Modules

| Module | Purpose |
| --- | --- |
| `TraceModule` | Record runtime events for scoring and refinement. |
| `BudgetGuardModule` | Enforce step, tool-call, token, and latency budgets. |
| `ToolExecutorModule` | Execute deterministic tools and later provider/runtime tools. |

## Optional Modules

| Module | Purpose |
| --- | --- |
| `PlannerModule` | Require or assist planning before execution. |
| `ContextManagerModule` | Summarize or select relevant context. |
| `ToolGatekeeperModule` | Check tool calls before execution. |
| `VerifierModule` | Check outputs after tool calls or before final answer. |
| `RetryControllerModule` | Decide when and how to retry. |
| `RecoveryModule` | Handle tool failures, format failures, and verifier failures. |
| `SubagentRouterModule` | Decide whether a subagent should be used. |

Small or unreliable models should compile to more control modules. Stronger
models should compile to lighter guardrails unless risk or task complexity
requires stronger control.
