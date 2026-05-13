"""Experimental policy-to-spec compiler API.

`HarnessSpec` remains useful for future runtime binding work. The trace-first
MVP only recommends policy diffs and does not require compiled specs.
"""

from adaharness.specs.compiler import compile_policy_to_spec
from adaharness.specs.harness_spec import ControllerSpec, HarnessSpec, ModuleSpec

__all__ = ["ControllerSpec", "HarnessSpec", "ModuleSpec", "compile_policy_to_spec"]
