from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from adaharness.analysis.traces import TraceEvent
from adaharness.analysis.validation import TraceValidationWarning


GROUP_FIELDS = ("model", "policy", "task_type")
UNKNOWN_GROUP_VALUE = "unknown"


@dataclass(frozen=True)
class TraceEventGroup:
    values: dict[str, str]
    events: tuple[TraceEvent, ...]

    def label(self) -> str:
        return ", ".join(f"{field}={value}" for field, value in self.values.items())


def normalize_group_by(group_by: str | list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    if group_by is None:
        return ()
    if isinstance(group_by, str):
        fields = tuple(field.strip() for field in group_by.split(",") if field.strip())
    else:
        fields = tuple(str(field).strip() for field in group_by if str(field).strip())
    unknown = [field for field in fields if field not in GROUP_FIELDS]
    if unknown:
        supported = ", ".join(GROUP_FIELDS)
        raise ValueError(f"Unsupported group-by field {unknown[0]!r}. Expected one of: {supported}")
    return tuple(dict.fromkeys(fields))


def group_trace_events(
    events: tuple[TraceEvent, ...],
    group_by: tuple[str, ...],
) -> tuple[TraceEventGroup, ...]:
    if not group_by:
        return ()
    grouped: dict[tuple[str, ...], list[TraceEvent]] = defaultdict(list)
    for event in events:
        key = tuple(_event_value(event, field) for field in group_by)
        grouped[key].append(event)
    groups = []
    for key, group_events in sorted(grouped.items(), key=lambda item: item[0]):
        groups.append(
            TraceEventGroup(
                values=dict(zip(group_by, key, strict=True)),
                events=tuple(group_events),
            )
        )
    return tuple(groups)


def mixed_group_warnings(
    events: tuple[TraceEvent, ...],
    *,
    grouped_fields: tuple[str, ...] = (),
) -> tuple[TraceValidationWarning, ...]:
    warnings = []
    for field in GROUP_FIELDS:
        if field in grouped_fields:
            continue
        values = sorted(
            {
                _event_value(event, field)
                for event in events
                if _event_value(event, field) != UNKNOWN_GROUP_VALUE
            }
        )
        if len(values) <= 1:
            continue
        sample = ", ".join(values[:5])
        warnings.append(
            TraceValidationWarning(
                code=f"mixed_{field}",
                severity="medium",
                message=(
                    f"Trace contains multiple {field} values; aggregate fit verdict may be misleading. "
                    f"Use --group-by {field} or include it in --group-by."
                ),
                evidence=(f"value_count={len(values)}", f"sample={sample}"),
            )
        )
    return tuple(warnings)


def _event_value(event: TraceEvent, field: str) -> str:
    value = getattr(event, field, None)
    if value is None:
        value = event.raw.get(field)
    return UNKNOWN_GROUP_VALUE if value is None else str(value)
