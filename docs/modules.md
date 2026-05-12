# Reference Runtime Modules

AdaHarness includes internal modules for its reference runtime. They validate
that a `HarnessPolicy` can compile into concrete controls and that those
controls can change runtime traces.

Production users should not have to reimplement their agent projects around
these modules. External projects should consume `HarnessSpec` through a future
runtime adapter and map controls to their own hooks, middleware, or config.

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

Small or unreliable models should compile to more controls. Stronger models
should compile to lighter guardrails unless risk or task complexity requires
stronger control.
