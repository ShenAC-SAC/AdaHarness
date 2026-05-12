from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import json
import tempfile
import textwrap
import unittest

from adaharness.cli import main


class CalibrateCliTests(unittest.TestCase):
    def test_calibrate_runs_project_adapter_and_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            package_dir = root / "my_agent"
            task_dir = root / "tasks"
            package_dir.mkdir()
            task_dir.mkdir()
            (package_dir / "__init__.py").write_text("", encoding="utf-8")
            (package_dir / "adaharness_adapter.py").write_text(
                textwrap.dedent(
                    """
                    from adaharness.adapters import AdapterCapabilities
                    from adaharness.policies.presets import BARE_POLICY
                    from adaharness.project import ProjectRunResult
                    from adaharness.runtime.tracing import RunTrace


                    class MyAgentAdapter:
                        name = "cli-agent"

                        def capabilities(self):
                            return AdapterCapabilities(
                                supports_pre_model_hook=True,
                                supports_post_model_hook=True,
                                supports_tool_interception=True,
                                supports_retry_loop=True,
                                supports_trace_export=True,
                            )

                        def run_task(self, task, *, binding=None):
                            trace = (
                                RunTrace.start(
                                    task_id=task.id,
                                    model_name=self.name,
                                    harness_name="host-runtime",
                                    policy=BARE_POLICY,
                                )
                                .add_event("host.task", target=task.target_capability)
                                .finish()
                            )
                            return ProjectRunResult(
                                task_id=task.id,
                                success=True,
                                score=0.8,
                                output="ok",
                                trace=trace,
                            )
                    """
                ),
                encoding="utf-8",
            )
            (task_dir / "tool.json").write_text(
                json.dumps(
                    {
                        "id": "tool",
                        "category": "tool",
                        "prompt": "Use a tool",
                        "difficulty": 0.5,
                        "target_capability": "tool_use",
                    }
                ),
                encoding="utf-8",
            )
            config_path = root / "adaharness.toml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "cli-agent"
                    adapter = "my_agent.adaharness_adapter:MyAgentAdapter"
                    taskset = "tasks"
                    artifact_dir = ".adaharness"

                    [defaults]
                    risk = "medium"
                    budget = "standard"
                    """
                ),
                encoding="utf-8",
            )

            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(["calibrate", "--config", str(config_path)])

            summary = json.loads(output.getvalue())
            artifact_dir = root / ".adaharness"

            self.assertEqual(exit_code, 0)
            self.assertEqual(summary["project"], "cli-agent")
            self.assertEqual(summary["task_count"], 1)
            self.assertTrue((artifact_dir / "profile.json").exists())
            self.assertTrue((artifact_dir / "policy.json").exists())
            self.assertTrue((artifact_dir / "spec.json").exists())
            self.assertTrue((artifact_dir / "binding.json").exists())
            self.assertTrue((artifact_dir / "report.md").exists())
