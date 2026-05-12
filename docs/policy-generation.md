# Policy Generation Experiments

AdaHarness treats generated harnesses as structured policy proposals, not code
edits.

## v0.6 Shape

```text
ModelProfile + trace summaries + taskset metadata
  -> external proposal JSON
  -> HarnessPolicy validation
  -> evaluation against rule-based policy
```

`PolicyProposal` wraps a `HarnessPolicy` with a rationale and source. The
executable policy schema stays unchanged so presets, traces, and metrics remain
stable.

Example:

```bash
uv run python - <<'PY'
from pathlib import Path
from adaharness.evals.task_schema import load_taskset
from adaharness.policies.proposals import load_policy_proposal, compare_policy_proposal
from adaharness.profiler.runner import run_profiler

profile = run_profiler("small-sim")
proposal = load_policy_proposal(Path("examples/policy_proposal.json"))
tasks = load_taskset(Path("tasks/eval"))
print(compare_policy_proposal(profile, proposal, tasks)["results"])
PY
```

## v0.7 Shape

Online adaptation starts with a deterministic `PolicyController` that observes
trace events and proposes policy changes. Runtime traces record `policy_change`
events; the controller does not mutate `HarnessPolicy` in place and does not
call a provider.
