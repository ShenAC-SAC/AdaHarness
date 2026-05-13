# Experimental Code Boundary

AdaHarness currently keeps earlier architecture work in the repository, but it
is not part of the trace-first MVP.

See `docs/adr/0008-keep-runtime-scaffolding-experimental.md` for the decision
record.

## Keep for Now

These packages should remain available while the analyzer proves value:

- `adaharness/adapters/`: runtime binding contract experiments.
- `adaharness/project/`: host-project calibration adapter prototype.
- `adaharness/specs/`: policy-to-spec compiler prototype.
- `adaharness/modules/`: reference controller/module implementations.
- `adaharness/harnesses/`: reference runtime and lab harness presets.

They are useful for tests, demos, and future design work. Deleting them now
would remove a tested path before we know which parts will become useful again.

## Not MVP

Do not promote these packages in the main user flow:

- automatic runtime control
- required project adapters
- hook binding into external runtimes
- online policy adaptation
- compiled `HarnessSpec` as a required artifact

The MVP artifact is still:

```text
trace evidence -> metrics -> diagnosis -> suggested policy diff -> report
```

## Revisit Criteria

Keep the experimental layer only while it stays low-maintenance. Revisit deletion
or extraction if it starts blocking the trace analyzer, confusing users, or
forcing API compatibility before the MVP is validated.
