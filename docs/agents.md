# Agent Framework Compatibility

English | [简体中文](agents.zh-CN.md)

The launchers support Claude Code, Codex CLI, and Hermes Agent against the same
local model servers. Each framework uses a different API surface, so the
compatibility layer is framework-specific.

Everyday use:

```bash
llm start       # choose backend and existing model
llm agent       # choose Claude, Codex, or Hermes
```

| Framework | Required protocol | llama.cpp | vLLM | Strata | Ollama |
|---|---|---|---|---|---|
| Claude Code | Anthropic Messages `/v1/messages` | Native | Native | Native | Compatibility proxy |
| Codex CLI | OpenAI Responses `/v1/responses` | Current build | Native | Native | Built-in OSS provider |
| Hermes Agent | OpenAI Chat Completions | Native | Native | Native | Native |

## Start A Backend

```bash
llm serve llama-cpp qwen3.5-4b
```

The model must support tool calling. For llama.cpp, use a current build
because older binaries may only expose Chat Completions.

## Claude Code

```bash
llm claude --backend llama-cpp --model qwen3.5-4b
```

Claude Code connects directly to the Anthropic endpoint for llama.cpp, vLLM,
and Strata. Ollama retains the compatibility proxy.

## Codex CLI

```bash
llm codex --backend llama-cpp --model qwen3.5-4b
llm codex --backend vllm --model Qwen3.5-4B
llm codex --backend strata --model q2_0
llm codex --backend ollama --model qwen3.5:4b
```

For custom providers, Codex currently uses the Responses API. The wrapper
supplies:

- provider base URL
- `wire_api = "responses"`
- local API key environment variable
- selected model
- `model_context_window`, defaulting to 32K

Use `--context` to match the backend:

```bash
llm codex --backend llama-cpp --model qwen3.5-4b --context 65536
```

The official Codex configuration reference documents custom model providers
and the Responses transport:
<https://developers.openai.com/codex/config-reference>

## Hermes Agent

```bash
llm hermes --backend llama-cpp --model qwen3.5-4b
```

The wrapper configures Hermes' custom provider:

```text
OPENAI_BASE_URL=http://127.0.0.1:8080/v1
OPENAI_API_KEY=local
provider=main
```

The same command works with vLLM, Strata, and Ollama. Hermes documents custom
OpenAI-compatible endpoints as a first-class provider.

## Agent Safety

These frameworks can edit files and execute commands. Use Git, keep approval
prompts enabled, and work in a disposable branch or sandbox while evaluating a
small local model. API compatibility does not guarantee reliable multi-step
tool use.
