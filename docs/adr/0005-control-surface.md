# ADR 0005: Treat Harness Specs as a Control Surface

## Status

Superseded for MVP by ADR 0007 and ADR 0008. Controller-oriented specs remain a
future experimental direction, not the current user path.

## Context

The first policy-to-spec compiler represented harness behavior mostly as enabled
or disabled modules. That is useful for a reference runtime, but too weak as the
main product abstraction. Real agent runtimes need to know not only whether a
planner or verifier exists, but how strong it is, when it triggers, who has
authority, what budget applies, and how failures escalate.

If AdaHarness remains module-centric, it risks becoming either a shallow
recommendation tool or a replacement runtime. The project goal is different:
compile model-aware harness control into runtime-neutral artifacts.

## Decision

AdaHarness will treat `HarnessSpec` as a controller-oriented control surface.
Modules remain implementation details for the reference runtime.

The stable semantic layer is:

```text
ModelProfile + TaskProfile + Risk + Budget
  -> HarnessPolicy
  -> HarnessSpec.controllers
  -> RuntimeBinding
```

Controller specs should describe levels, modes, triggers, budgets, authority,
scope, and escalation. Runtime adapters bind those controller specs to hooks or
middleware in an external runtime.

## Consequences

- `HarnessSpec` must support controller-level fields in addition to legacy
  module fields.
- Existing module-based tests and reference runtime behavior should keep working
  while the controller contract is introduced.
- Reports and docs should emphasize control strength and controller diffs rather
  than only enabled and disabled modules.
- Runtime adapters should bind controllers first and treat modules as a
  compatibility view.
