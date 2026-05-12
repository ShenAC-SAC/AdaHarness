from __future__ import annotations

from adaharness.adapters import RuntimeBinding, bind_runtime
from adaharness.evals.task_schema import EvalTask
from adaharness.policies.generator import recommend_policy
from adaharness.policies.schema import BudgetLevel, RiskLevel
from adaharness.profiler.profile_schema import CAPABILITY_FIELDS, ModelProfile
from adaharness.project.adapter import ProjectAgentAdapter, ProjectRunResult
from adaharness.project.result import AgentSystemProfile, CalibrationResult
from adaharness.specs import compile_policy_to_spec


def calibrate_project(
    adapter: ProjectAgentAdapter,
    tasks: list[EvalTask],
    *,
    risk: RiskLevel = "medium",
    budget: BudgetLevel = "standard",
) -> CalibrationResult:
    """Run project tasks and compile policy artifacts from project evidence."""
    if not tasks:
        raise ValueError("tasks must contain at least one calibration task")

    runs = tuple(adapter.run_task(task) for task in tasks)
    profile = _profile_from_runs(adapter, tasks, runs)
    recommendation = recommend_policy(profile.model_profile, risk=risk, budget=budget)
    spec = compile_policy_to_spec(
        recommendation.policy,
        name=f"{adapter.name}_controls",
        metadata={
            "project": adapter.name,
            "calibration_task_count": len(tasks),
        },
    )
    binding = bind_runtime(spec, capabilities=adapter.capabilities(), runtime=adapter.name)
    report = _render_calibration_report(profile, recommendation.rationale, binding)
    return CalibrationResult(
        profile=profile,
        recommendation=recommendation,
        spec=spec,
        binding=binding,
        runs=runs,
        report=report,
    )


def _profile_from_runs(
    adapter: ProjectAgentAdapter,
    tasks: list[EvalTask],
    runs: tuple[ProjectRunResult, ...],
) -> AgentSystemProfile:
    scores_by_capability = {
        capability: [
            run.score
            for task, run in zip(tasks, runs, strict=True)
            if task.target_capability == capability
        ]
        for capability in CAPABILITY_FIELDS
    }
    capability_scores = {
        capability: _average(scores) if scores else 0.5
        for capability, scores in scores_by_capability.items()
    }
    failures = tuple(
        error
        for run in runs
        for error in run.errors
    )
    model_profile = ModelProfile(
        model_name=adapter.name,
        weaknesses=tuple(
            capability
            for capability, score in capability_scores.items()
            if score < 0.5
        ),
        **capability_scores,
    )
    return AgentSystemProfile(
        project_name=adapter.name,
        model_profile=model_profile,
        task_count=len(tasks),
        success_rate=sum(1 for run in runs if run.success) / len(runs),
        runtime_capabilities=adapter.capabilities().to_dict(),
        failure_modes=failures,
    )


def _average(values: list[float]) -> float:
    return sum(values) / len(values)


def _render_calibration_report(
    profile: AgentSystemProfile,
    rationale: tuple[str, ...],
    binding: RuntimeBinding,
) -> str:
    lines = [
        f"# AdaHarness Calibration: {profile.project_name}",
        "",
        f"- Task count: {profile.task_count}",
        f"- Success rate: {profile.success_rate:.2f}",
        f"- Capability average: {profile.model_profile.capability_average:.2f}",
        "",
        "## Recommendation Rationale",
        "",
    ]
    lines.extend(f"- {item}" for item in rationale)
    lines.extend(
        [
            "",
            "## Runtime Binding",
            "",
            f"- Runtime: {binding.runtime}",
            f"- Bound controllers: {', '.join(binding.enabled_features) or 'none'}",
        ]
    )
    if binding.unsupported_controllers:
        lines.append(f"- Unsupported controllers: {', '.join(binding.unsupported_controllers)}")
    return "\n".join(lines)
