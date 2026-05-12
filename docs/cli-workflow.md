# CLI Workflow

The AdaHarness CLI should be used inside an agent project as a calibration,
validation, trace-import, and artifact-generation tool. It is not intended to be
the production agent runner.

## Project-Local Path

The intended flow is:

```text
calibrate -> recommend -> compile -> bind -> validate -> report
```

A host project should keep ownership of model credentials, prompts, tools, and
runtime state. AdaHarness should call a project adapter or consume exported
traces, then produce artifacts under `.adaharness/`:

```text
.adaharness/
  traces/
  profile.json
  policy.json
  spec.json
  binding.json
  report.md
```

Current and planned commands:

```bash
adaharness calibrate --config adaharness.toml
adaharness bind --config adaharness.toml --spec .adaharness/spec.json
adaharness validate --config adaharness.toml --binding .adaharness/binding.json
```

`calibrate` is implemented first. It loads the project adapter, runs the taskset,
and writes profile, policy, spec, binding, run, and report artifacts. `bind` and
`validate` are planned follow-ups around the same adapter contract.

## Project Configuration

For embedded use, config should describe the project adapter and runtime
capabilities, not duplicate provider keys already owned by the host project.

```toml
[project]
name = "my-agent"
adapter = "my_agent.adaharness_adapter:MyAgentAdapter"
taskset = "tests/adaharness_tasks"

[defaults]
risk = "medium"
budget = "standard"

[capabilities]
supports_pre_model_hook = true
supports_post_model_hook = true
supports_tool_interception = true
supports_retry_loop = true
supports_trace_export = true
```

## Lab Commands

Existing commands such as `profile`, `compare`, `assemble`, and reference
`run` remain useful for AdaHarness development, examples, and CI smoke tests:

```bash
adaharness profile --model example-model
adaharness compare --model example-model --taskset tasks/eval
adaharness assemble --policy runs/policy.json --out runs/spec.json
adaharness run --provider mock --model mock-model --harness-spec runs/spec.json --task tasks/eval
```

These commands should not be presented as the main production integration path.
