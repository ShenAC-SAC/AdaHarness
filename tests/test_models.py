import unittest

from adaharness.models.base import ModelConfig
from adaharness.models.factory import build_model_client, build_model_config
from adaharness.models.mock import MockModelClient


class ModelClientTests(unittest.TestCase):
    def test_mock_client_returns_structured_response(self) -> None:
        client = MockModelClient(model_name="mock", responses=("done",))

        response = client.complete([{"role": "user", "content": "hello world"}])

        self.assertEqual(response.text, "done")
        self.assertIsNotNone(response.usage)
        self.assertEqual(response.usage.input_tokens, 2)
        self.assertEqual(response.usage.output_tokens, 1)

    def test_build_model_config_rejects_unknown_provider(self) -> None:
        with self.assertRaises(ValueError):
            build_model_config("model", provider="unknown")

    def test_build_model_client_uses_mock_for_synthetic_provider(self) -> None:
        client = build_model_client(ModelConfig(name="synthetic-model"))

        response = client.complete([{"role": "user", "content": "ping"}])

        self.assertEqual(response.text, "mock response")

    def test_openai_compatible_config_preserves_non_openai_base_url(self) -> None:
        config = build_model_config(
            "deepseek-chat",
            provider="openai-compatible",
            base_url="https://provider.example/v1",
        )

        self.assertEqual(config.provider, "openai-compatible")
        self.assertEqual(config.name, "deepseek-chat")
        self.assertEqual(config.base_url, "https://provider.example/v1")
