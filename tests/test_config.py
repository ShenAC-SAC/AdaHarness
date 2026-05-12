from pathlib import Path
import os
import tempfile
import unittest

from adaharness.config import load_config


class ConfigTests(unittest.TestCase):
    def test_load_config_resolves_model_and_env_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = root / "adaharness.toml"
            env_path = root / ".env"
            config_path.write_text(
                """
[providers.deepseek]
type = "openai-compatible"
base_url = "https://api.deepseek.com/v1"
api_key_env = "DEEPSEEK_API_KEY"

[models.deepseek-chat]
provider = "deepseek"

[defaults]
risk = "high"
budget = "constrained"
taskset = "tasks/profiler"
""",
                encoding="utf-8",
            )
            env_path.write_text("DEEPSEEK_API_KEY=test-key\n", encoding="utf-8")
            old_value = os.environ.pop("DEEPSEEK_API_KEY", None)
            try:
                config = load_config(config_path)
                model = config.resolve_model("deepseek-chat")
            finally:
                if old_value is not None:
                    os.environ["DEEPSEEK_API_KEY"] = old_value
                else:
                    os.environ.pop("DEEPSEEK_API_KEY", None)

        self.assertEqual(config.defaults.risk, "high")
        self.assertEqual(model.provider, "openai-compatible")
        self.assertEqual(model.base_url, "https://api.deepseek.com/v1")
        self.assertEqual(model.api_key, "test-key")

    def test_missing_model_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "adaharness.toml"
            config_path.write_text("[providers.mock]\ntype = \"mock\"\n", encoding="utf-8")
            config = load_config(config_path)

        with self.assertRaises(ValueError):
            config.resolve_model("missing")
