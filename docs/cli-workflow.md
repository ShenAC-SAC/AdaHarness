# CLI Workflow

The primary AdaHarness workflow is `profile -> recommend -> assemble -> run`.
`compare` remains a research and validation command.

## Primary Path

```bash
adaharness profile \
  --model qwen-local \
  --provider openai-compatible \
  --taskset tasks/profiler \
  --out runs/qwen-profile.json

adaharness recommend \
  --profile runs/qwen-profile.json \
  --taskset tasks/bench-v0.1 \
  --risk medium \
  --budget standard \
  --out runs/qwen-policy.json

adaharness assemble \
  --policy runs/qwen-policy.json \
  --out runs/qwen-harness-spec.json

adaharness run \
  --live \
  --provider openai-compatible \
  --model qwen-local \
  --harness-spec runs/qwen-harness-spec.json \
  --task tasks/eval/recovery_001.json \
  --out runs/qwen-run.json
```

## Validation Path

```bash
adaharness compare \
  --model qwen-local \
  --harnesses bare,light,structured,strong,adaptive \
  --taskset tasks/bench-v0.1
```

`compare` helps validate whether a policy or spec is effective. It should not
replace policy and spec artifacts.
