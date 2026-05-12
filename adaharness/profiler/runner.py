from __future__ import annotations

from pathlib import Path

from adaharness.models.base import ModelConfig
from adaharness.profiler.profile_schema import CAPABILITY_FIELDS, CapabilityScore, ModelProfile
from adaharness.profiler.scoring import synthetic_profile
from adaharness.profiler.tasks import ProfilerTask, load_profiler_taskset


def run_profiler(model: str | ModelConfig, taskset: Path | None = None) -> ModelProfile:
    """Run the placeholder profiler.

    The profiler is task-backed but deterministic until v0.3 connects task
    execution to live model clients.
    """
    model_name = model.name if isinstance(model, ModelConfig) else model
    profile = synthetic_profile(model_name)
    if taskset is None:
        return profile

    tasks = load_profiler_taskset(taskset)
    return score_profile_from_tasks(profile, tasks)


def score_profile_from_tasks(base_profile: ModelProfile, tasks: list[ProfilerTask]) -> ModelProfile:
    tasks_by_capability = {
        capability: [task for task in tasks if task.capability == capability]
        for capability in CAPABILITY_FIELDS
    }
    scores = {
        capability: _score_capability(base_profile, capability, capability_tasks)
        for capability, capability_tasks in tasks_by_capability.items()
    }
    weaknesses = tuple(name for name, score in scores.items() if score.score < 0.60)
    controls = recommended_controls_for_weaknesses(weaknesses)

    return ModelProfile(
        model_name=base_profile.model_name,
        planning=scores["planning"].score,
        tool_use=scores["tool_use"].score,
        instruction_following=scores["instruction_following"].score,
        self_verification=scores["self_verification"].score,
        context_management=scores["context_management"].score,
        recovery=scores["recovery"].score,
        cost_sensitivity=scores["cost_sensitivity"].score,
        delegation=scores["delegation"].score,
        scores=scores,
        weaknesses=weaknesses,
        recommended_controls=controls,
    )


def recommended_controls_for_weaknesses(weaknesses: tuple[str, ...]) -> tuple[str, ...]:
    controls_by_weakness = {
        "planning": "explicit_planning",
        "tool_use": "strict_tool_gatekeeping",
        "instruction_following": "schema_scaffolding",
        "self_verification": "post_answer_verification",
        "context_management": "context_summarization",
        "recovery": "bounded_retry",
        "cost_sensitivity": "budget_guardrails",
        "delegation": "delegation_brief_template",
    }
    return tuple(controls_by_weakness[name] for name in weaknesses)


def _score_capability(
    base_profile: ModelProfile,
    capability: str,
    tasks: list[ProfilerTask],
) -> CapabilityScore:
    base_score = getattr(base_profile, capability)
    if not tasks:
        return CapabilityScore(
            name=capability,
            score=base_score,
            confidence=0.35,
            evidence=(f"no profiler task for {capability}; retained synthetic estimate",),
        )

    task_scores = [_estimate_task_score(base_score, task.difficulty) for task in tasks]
    score = sum(task_scores) / len(task_scores)
    confidence = min(0.95, 0.45 + len(tasks) * 0.15)
    evidence = tuple(
        f"{task.id}: difficulty={task.difficulty:.2f}, estimated_score={task_score:.2f}"
        for task, task_score in zip(tasks, task_scores, strict=True)
    )
    failed_cases = tuple(
        task.id
        for task, task_score in zip(tasks, task_scores, strict=True)
        if task_score < task.difficulty
    )
    return CapabilityScore(
        name=capability,
        score=round(score, 3),
        confidence=round(confidence, 3),
        evidence=evidence,
        failed_cases=failed_cases,
    )


def _estimate_task_score(base_score: float, difficulty: float) -> float:
    margin = base_score - difficulty
    adjusted = base_score + margin * 0.12
    return max(0.0, min(1.0, adjusted))
