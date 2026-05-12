from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from adaharness.analysis.diagnostics import DiagnosticSignal


@dataclass(frozen=True)
class PolicyChange:
    field: str
    from_value: str
    to_value: str
    reason: str
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", tuple(self.evidence))

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["from"] = data.pop("from_value")
        data["to"] = data.pop("to_value")
        return data


def recommend_policy_changes(
    signals: tuple[DiagnosticSignal, ...],
    *,
    current_policy: dict[str, Any] | None = None,
) -> tuple[PolicyChange, ...]:
    current = current_policy or {}
    changes: list[PolicyChange] = []
    for signal in signals:
        change = _change_for_signal(signal, current)
        if change is not None:
            changes.append(change)
    return tuple(_dedupe(changes))


def _change_for_signal(signal: DiagnosticSignal, current: dict[str, Any]) -> PolicyChange | None:
    if signal.kind == "balanced":
        return None
    field = signal.control
    old = _current_value(current, field)
    if signal.kind == "overconstraint":
        new = _weaken(field, old)
    elif signal.kind == "underconstraint":
        new = _strengthen(field, old)
    else:
        return None
    if new == old:
        return None
    return PolicyChange(
        field=field,
        from_value=old,
        to_value=new,
        reason=signal.message,
        evidence=signal.evidence,
    )


def _current_value(policy: dict[str, Any], field: str) -> str:
    aliases = {
        "planning_control": ("planning_control", "planning_depth"),
        "verification_control": ("verification_control", "verifier_strength"),
        "retry_control": ("retry_control", "retry_policy"),
        "tool_control": ("tool_control", "tool_gatekeeping"),
    }
    for key in aliases.get(field, (field,)):
        if key in policy:
            return str(policy[key])
    return "unknown"


def _weaken(field: str, value: str) -> str:
    orders = {
        "planning_control": ("off", "hint", "light", "explicit", "strict"),
        "verification_control": ("off", "final_only", "selective", "always"),
        "retry_control": ("none", "single", "bounded", "aggressive"),
        "tool_control": ("none", "moderate", "strict"),
    }
    return _step(field, value, orders, direction=-1, fallback="selective")


def _strengthen(field: str, value: str) -> str:
    orders = {
        "planning_control": ("off", "hint", "light", "explicit", "strict"),
        "verification_control": ("off", "final_only", "selective", "always"),
        "retry_control": ("none", "single", "bounded", "aggressive"),
        "tool_control": ("none", "moderate", "strict"),
    }
    return _step(field, value, orders, direction=1, fallback="bounded")


def _step(
    field: str,
    value: str,
    orders: dict[str, tuple[str, ...]],
    *,
    direction: int,
    fallback: str,
) -> str:
    order = orders.get(field)
    if order is None:
        return value
    if value == "unknown":
        return _unknown_default(field, direction)
    if value == "none" and "off" in order:
        value = "off"
    if value not in order:
        return fallback if fallback in order else value
    index = max(0, min(len(order) - 1, order.index(value) + direction))
    return order[index]


def _unknown_default(field: str, direction: int) -> str:
    if direction < 0:
        return {
            "planning_control": "light",
            "verification_control": "selective",
            "retry_control": "bounded",
            "tool_control": "moderate",
        }.get(field, "unknown")
    return {
        "planning_control": "explicit",
        "verification_control": "selective",
        "retry_control": "bounded",
        "tool_control": "moderate",
    }.get(field, "unknown")


def _dedupe(changes: list[PolicyChange]) -> list[PolicyChange]:
    deduped: dict[str, PolicyChange] = {}
    for change in changes:
        deduped.setdefault(change.field, change)
    return list(deduped.values())
