# Model Support Strategy

AdaHarness should support models by protocol and deployment shape, not by adding
a bespoke adapter for every model brand.

## Supported Boundaries

| Boundary | Use for | Notes |
| --- | --- | --- |
| `synthetic` | deterministic lab profiling | No network or credentials. |
| `mock` | tests and examples | Returns structured fake responses. |
| `openai-compatible` | OpenAI, DeepSeek, Qwen-compatible APIs, OpenRouter, vLLM, LM Studio | Use `--base-url` for non-OpenAI endpoints. |
| `anthropic` | Claude models through Anthropic's SDK | Useful as a strong proprietary baseline. |
| `local` | Ollama-style local `/api/chat` deployments | Other local servers may fit `openai-compatible`. |

## Research Framing

OpenAI and Anthropic models are not the only target. They are strong baselines
and already ship with provider-specific agent tooling. AdaHarness is most
interesting when it can measure whether extra planning, retries, tool gating, or
verification help models with less mature native harnesses.

The first priority is therefore broad protocol coverage:

- OpenAI-compatible cloud providers, including DeepSeek- and Qwen-compatible
  endpoints.
- Local deployments served through Ollama, vLLM, LM Studio, or similar tools.
- Proprietary frontier models as comparison baselines.

## Adapter Rule

Add a native provider adapter only when the provider has meaningful protocol
differences that cannot be represented by `openai-compatible`, `anthropic`, or
`local`. Otherwise, keep the implementation at the protocol layer and document
the provider-specific `--base-url` and environment setup.

## Project Configuration

Provider URLs and provider-specific API key environment variables may live in
`adaharness.toml` for lab commands that call models directly:

```toml
[providers.deepseek]
type = "openai-compatible"
base_url = "https://api.deepseek.com/v1"
api_key_env = "DEEPSEEK_API_KEY"

[models.deepseek-chat]
provider = "deepseek"
```

`.env` may define `DEEPSEEK_API_KEY=...`. `config inspect` reports whether a key
is configured without printing the secret value.
