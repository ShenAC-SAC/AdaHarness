from __future__ import annotations

from pathlib import Path
import json

from adaharness.integrations.base import ExternalTraceAdapter
from adaharness.integrations.generic_trace import GenericJSONTraceAdapter
from adaharness.runtime.tracing import RunTrace


DEFAULT_TRACE_ADAPTERS: tuple[ExternalTraceAdapter, ...] = (GenericJSONTraceAdapter(),)


def import_external_trace(
    path: Path,
    *,
    adapters: tuple[ExternalTraceAdapter, ...] = DEFAULT_TRACE_ADAPTERS,
) -> RunTrace:
    source = json.loads(path.read_text(encoding="utf-8"))
    for adapter in adapters:
        if adapter.can_parse(source):
            return adapter.parse(source)
    raise ValueError(f"No external trace adapter could parse {path}")
