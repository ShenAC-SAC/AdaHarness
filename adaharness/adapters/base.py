from __future__ import annotations

from typing import Any, Protocol

from adaharness.adapters.binding import AdapterCapabilities, RuntimeBinding
from adaharness.specs.harness_spec import HarnessSpec


class RuntimeAdapter(Protocol):
    name: str

    def inspect(self, target: Any | None = None) -> AdapterCapabilities:
        ...

    def bind(self, spec: HarnessSpec, target: Any | None = None) -> RuntimeBinding:
        ...
