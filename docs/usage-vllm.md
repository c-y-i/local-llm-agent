# Using vLLM

English | [简体中文](usage-vllm.zh-CN.md)

vLLM serves OpenAI- and Anthropic-compatible APIs and is intended for
high-throughput, GPU-resident inference. It loads Hugging Face model weights,
AWQ/GPTQ checkpoints, or converted local model directories. It does not load
GGUF files.

## Install

Install vLLM in an isolated Python environment:

```bash
llm install vllm
source "$HOME/LLM/venvs/vllm/bin/activate"
python -m pip install --upgrade pip
```

`llm` uses `LLM_VENVS_DIR`, not the repository, for the virtual environment.
Customize `LLM_ROOT` in `.env` if that location should be different.

Check the installation:

```bash
vllm --version
```

vLLM is most useful with a model that fits fully in GPU memory plus its KV
cache. Set `VLLM_BIN` if it is installed outside `PATH`.

## Serve

```bash
./scripts/vllm/serve.sh Qwen/Qwen3.5-4B
```

The wrapper defaults to port `8000` and model ID `Qwen3.5-4B`.

Important options:

| Variable | Default | Purpose |
|---|---|---|
| `VLLM_PORT` | `8000` | Server port |
| `VLLM_HOST` | `127.0.0.1` | Bind address |
| `VLLM_SERVED_MODEL_NAME` | model basename | Stable model ID used by clients |
| `VLLM_TOOL_CALL_PARSER` | `qwen3_coder` | Parser required for agent tool calls |
| `VLLM_REASONING_PARSER` | unset | Model-specific reasoning parser |
| `VLLM_MAX_MODEL_LEN` | model default | Maximum context length |
| `VLLM_GPU_MEMORY_UTILIZATION` | vLLM default | Fraction of VRAM reserved for vLLM |
| `VLLM_EXTRA_ARGS` | unset | Additional space-separated `vllm serve` flags |

Qwen3, Qwen3.5, and Qwen3-Coder tool calls generally use the `qwen3_coder`
parser. Other models require the parser documented by vLLM, such as `hermes`
or `mistral`. Tool calls do not work reliably without
`--enable-auto-tool-choice` and the matching parser.

Example with an explicit context ceiling:

```bash
VLLM_MAX_MODEL_LEN=16384 ./scripts/vllm/serve.sh Qwen/Qwen3.5-4B
```

## Endpoints

```text
OpenAI:    http://127.0.0.1:8000/v1
Anthropic: http://127.0.0.1:8000
Messages:  http://127.0.0.1:8000/v1/messages
Models:    http://127.0.0.1:8000/v1/models
```

Anthropic clients use the base URL without `/v1`.

## Claude Code

```bash
./scripts/claude/claude-local.sh --backend vllm --model Qwen3.5-4B
```

The launcher exports the required Anthropic base URL, authentication token,
model aliases, and disables Claude Code's changing attribution header for
better prefix-cache reuse.

## Memory Note

On a 6 GB GPU, choose a 4-bit model whose weights leave room for the KV cache.
Use a shorter `VLLM_MAX_MODEL_LEN` when the server cannot allocate the KV cache.
Single-user laptop inference is generally better served by llama.cpp or
Ollama; vLLM becomes worthwhile with concurrent requests or a larger GPU.
