# Backends And Storage

English | [简体中文](backends.zh-CN.md)

## Supported Scope

llama.cpp is the primary backend. Ollama is supported as a secondary backend
and shared model store. vLLM and Strata are deferred for now.

## Prerequisites

Common requirements:

- Python 3 with `venv`
- Git
- curl
- CMake, Make, and a C/C++ compiler
- The Claude Code, Codex CLI, or Hermes CLI for the agent you intend to use

For NVIDIA acceleration:

- an NVIDIA driver visible through `nvidia-smi`
- a CUDA-capable llama.cpp build

Check the machine:

```bash
./scripts/setup/check-prereqs.sh
llm doctor
```

## Storage

```text
~/LLM/
  models/        # canonical GGUF files
  llama.cpp/     # llama.cpp source and build
  ollama/        # Ollama service state and model links
  .venv/         # managed Python environment
  run/           # logs and PID files
  codex-local/   # isolated Codex state
  hermes-local/  # isolated Hermes state
```

Override `LLM_ROOT` or individual paths in `.env`. Never place model weights,
engine builds, caches, virtualenvs, or credentials in the Git repository.

## llama.cpp

Build:

```bash
source .venv/bin/activate
llm build llama-cpp
```

Force CPU-only:

```bash
llm build llama-cpp --cuda OFF
```

Start a model:

```bash
llm start llama-cpp qwen3.5-4b-official-Q4_K_M
```

Direct agent commands launch the preferred installed GGUF automatically when
needed:

```bash
hermes-local
codex-local
claude-local
```

The default endpoint is `http://127.0.0.1:8080`.

## Adding A GGUF

Download a `*.gguf` file into `$LLM_MODELS_DIR` and use the filename without
`.gguf` as the model identifier:

```text
~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf
```

Example direct Hugging Face download:

```bash
curl -fL --retry 5 -C - \
  -o ~/LLM/models/qwen3.5-2b-official-Q4_K_M.gguf.part \
  https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/main/Qwen3.5-2B-Q4_K_M.gguf
mv ~/LLM/models/qwen3.5-2b-official-Q4_K_M.gguf.part \
  ~/LLM/models/qwen3.5-2b-official-Q4_K_M.gguf
```

Verify a download against the checksum published by Hugging Face before using
it.

## Ollama

Install and configure:

```bash
llm install ollama
./scripts/setup/configure-ollama.sh
```

Warm an existing model:

```bash
llm start ollama qwen3.5-4b-official:latest
```

Ollama can share the canonical GGUF with llama.cpp through the helpers under
`scripts/ollama/`; do not keep duplicate multi-gigabyte copies.

## Lifecycle And Logs

Only one llama.cpp server can provide the model for port 8080 at a time.
Background agent launches store the PID in `$LLM_ROOT/run/llama-server.pid`
and logs in `$LLM_ROOT/run/llama-server.log`.

Ollama is managed as a separate daemon. When `llm start ollama` needs to start
it, the PID is stored in `$LLM_ROOT/run/ollama.pid` and logs are appended to
`$LLM_ROOT/run/ollama.log`.

Useful checks:

```bash
llm status
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8080/props
curl -s http://127.0.0.1:8080/metrics
curl -s http://127.0.0.1:11434/api/ps
llm logs --backend llama-cpp
llm logs --backend ollama --follow
```
