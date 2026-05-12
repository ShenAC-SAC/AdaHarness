from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class TraceEvent:
    event_type: str
    payload: dict[str, Any]
    timestamp: str

    @classmethod
    def create(cls, event_type: str, payload: dict[str, Any]) -> "TraceEvent":
        return cls(
            event_type=event_type,
            payload=payload,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
