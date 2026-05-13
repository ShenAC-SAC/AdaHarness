"""Experimental host-project calibration API.

The current MVP analyzes exported traces. Project adapters are retained as a
future integration path, not as a required way to use AdaHarness.
"""

from adaharness.project.adapter import ProjectAgentAdapter, ProjectRunResult
from adaharness.project.calibration import calibrate_project
from adaharness.project.result import AgentSystemProfile, CalibrationResult

__all__ = [
    "AgentSystemProfile",
    "CalibrationResult",
    "ProjectAgentAdapter",
    "ProjectRunResult",
    "calibrate_project",
]
