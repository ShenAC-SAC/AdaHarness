# Harness Policy Layer

AdaHarness can eventually become a policy layer, but the MVP is deliberately
lighter: it recommends policy changes from trace evidence instead of controlling
the runtime.

## MVP Boundary

```text
Trace evidence -> Harness diagnosis -> Suggested policy diff
```

The host agent project keeps ownership of:

- model providers and credentials
- prompts and tools
- runtime hooks
- state, memory, streaming, and approvals
- production execution

AdaHarness only reads traces and returns evidence-backed recommendations.

## Experimental Boundary

The earlier policy-layer path remains experimental:

```text
HarnessPolicy -> HarnessSpec -> RuntimeBinding -> runtime hooks
```

This can become useful later, but it should not be required for early users.
Users should get value by exporting traces, not by adopting AdaHarness as a
runtime dependency.

## Policy Diff

The MVP policy artifact should be a suggestion, not an enforcement mechanism:

```json
{
  "verification_control": {
    "from": "always",
    "to": "selective",
    "reason": "Verifier catch rate was low while verifier cost share was high."
  }
}
```

This keeps adoption low-friction and makes the recommendation auditable.
