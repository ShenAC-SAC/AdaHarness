from pathlib import Path
import json
import tempfile
import unittest

from adaharness.integrations import import_external_trace


class IntegrationTraceTests(unittest.TestCase):
    def test_import_generic_external_trace(self) -> None:
        source = {
            "run_id": "external_1",
            "task_id": "task_1",
            "model_name": "model-x",
            "harness_name": "runtime-y",
            "events": [
                {"type": "llm_call", "total_tokens": 12},
                {"event_type": "verifier.check", "payload": {"verdict": "passed"}},
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "external.json"
            path.write_text(json.dumps(source), encoding="utf-8")

            trace = import_external_trace(path)

        self.assertEqual(trace.run_id, "external_1")
        self.assertEqual(trace.model_name, "model-x")
        self.assertEqual(trace.events[0].event_type, "llm_call")
        self.assertEqual(trace.events[0].payload["total_tokens"], 12)

