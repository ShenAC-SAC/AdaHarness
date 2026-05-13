"""Reference harness modules for experimental runtime assembly.

These modules are not required by the trace-first analyzer. They are retained to
support reference runtime tests and future controller experiments.
"""

from adaharness.modules.base import HarnessModule
from adaharness.modules.registry import DEFAULT_MODULE_REGISTRY, ModuleRegistry

__all__ = ["DEFAULT_MODULE_REGISTRY", "HarnessModule", "ModuleRegistry"]
