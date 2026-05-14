from pathlib import Path
import json
import tempfile
import unittest

from adaharness import TraceRecorder, analyze_traces


class PublicApiTests(unittest.TestCase):
    def test_analyze_traces_returns_report_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            trace_path = root / "trace.jsonl"
            policy_path = root / "policy.json"
            trace_path.write_text(
                "\n".join(
                    json.dumps(event)
                    for task_id in ["t1", "t2", "t3", "t4", "t5"]
                    for event in [
                        {"task_id": task_id, "event": "verifier", "status": "pass", "cost": 0.01},
                        {"task_id": task_id, "event": "final", "success": True, "cost": 0.02},
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            policy_path.write_text(json.dumps({"verification_control": "always"}), encoding="utf-8")

            data = analyze_traces([trace_path], current_policy=policy_path)

        self.assertIn("AdaHarness Drift Report", data["report"])
        self.assertEqual(data["metrics"]["task_count"], 5)
        self.assertEqual(data["fit_verdict"]["status"], "likely_overcontrolled")
        self.assertEqual(data["fit_verdict"]["primary_controls"], ("verification_control",))
        self.assertEqual(data["group_by"], [])
        self.assertEqual(data["groups"], [])
        self.assertEqual(data["policy_diff"]["changes"][0]["field"], "verification_control")
        self.assertEqual(data["policy_diff"]["changes"][0]["from"], "always")
        self.assertEqual(data["policy_diff"]["changes"][0]["to"], "selective")

    def test_analyze_traces_groups_by_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = Path(tmpdir) / "trace.jsonl"
            records = []
            for task_id in ["old-1", "old-2", "old-3", "old-4", "old-5"]:
                records.extend(
                    [
                        {
                            "task_id": task_id,
                            "model": "old-model",
                            "event": "verifier",
                            "status": "pass",
                            "cost": 0.01,
                        },
                        {
                            "task_id": task_id,
                            "model": "old-model",
                            "event": "final",
                            "success": True,
                            "cost": 0.02,
                        },
                    ]
                )
            for task_id in ["new-1", "new-2"]:
                records.extend(
                    [
                        {
                            "task_id": task_id,
                            "model": "new-model",
                            "event": "tool_call",
                            "status": "failed",
                        },
                        {
                            "task_id": task_id,
                            "model": "new-model",
                            "event": "final",
                            "success": False,
                        },
                    ]
                )
            trace_path.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )

            data = analyze_traces([trace_path], group_by="model")

        statuses = {
            group["group"]["model"]: group["fit_verdict"]["status"]
            for group in data["groups"]
        }
        warning_codes = [warning["code"] for warning in data["trace_warnings"]]
        self.assertEqual(data["group_by"], ["model"])
        self.assertEqual(statuses["old-model"], "likely_overcontrolled")
        self.assertEqual(statuses["new-model"], "likely_undercontrolled")
        self.assertNotIn("mixed_model", warning_codes)
        self.assertIn("Group: model=old-model", data["report"])

    def test_analyze_traces_warns_when_multiple_models_are_not_grouped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = Path(tmpdir) / "trace.jsonl"
            trace_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "task_id": "t1",
                                "model": "old-model",
                                "event": "final",
                                "success": True,
                            }
                        ),
                        json.dumps(
                            {
                                "task_id": "t2",
                                "model": "new-model",
                                "event": "final",
                                "success": True,
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            data = analyze_traces([trace_path])

        warning_codes = [warning["code"] for warning in data["trace_warnings"]]
        self.assertIn("mixed_model", warning_codes)

    def test_top_level_exports_trace_recorder(self) -> None:
        self.assertIs(TraceRecorder, TraceRecorder)
