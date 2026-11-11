# local-llm-agent

English | [简体中文](README.zh-CN.md)

Run local coding models on your own hardware and connect them to Claude Code,
Codex CLI, or Hermes Agent. The repository contains code, documentation, and
small configuration files; model weights and runtime state live outside Git.

## Reference Setup And Tested Agents

The reference setup is an RTX 3050 Laptop GPU with 6 GB VRAM. The current
workflow has been tested end to end there with:

- Claude Code
- Codex CLI
- Hermes Agent

The shared tested backend was llama.cpp with official Qwen3.5-4B Q4_K_M.
Hermes was also verified with official Qwen3.5-2B, including large context
windows. These models are examples for this hardware tier, not requirements.
Machines with more VRAM and RAM can run larger and stronger models.

## Current Scope

| Component | Status | Endpoint |
|---|---|---|
| llama.cpp | Primary local backend | `http://127.0.0.1:8080` |
| Ollama | Secondary backend and model store | `http://127.0.0.1:11434` |
| Claude Code | Tested | llama.cpp native, Ollama through proxy |
| Codex CLI | Tested | llama.cpp Responses provider |
| Hermes Agent | Tested | OpenAI-compatible endpoint |
| vLLM | Deferred | Not part of the current hardware workflow |
| Strata | Deferred | Not part of the current hardware workflow |

Documentation and screenshots for older Cline, Copilot, control-panel,
portable-launcher, vLLM, and Strata workflows were removed for now. The docs
now describe the tested local-agent path only.

## Install

```bash
./scripts/setup/install-llm.sh
source .venv/bin/activate
llm --version
```

`llm` requires the managed Python environment. The direct agent commands
activate it automatically.

## Quick Start

Check prerequisites, build llama.cpp, and obtain a model:

```bash
./scripts/setup/check-prereqs.sh
source .venv/bin/activate
llm setup

curl -fL --retry 5 -C - \
  -o ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf.part \
  https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/main/Qwen3.5-4B-Q4_K_M.gguf
mv ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf.part \
  ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf
```

The download is about 2.6 GB. Qwen3.5-2B is a smaller alternative documented in
[`docs/models.md`](docs/models.md). Install the Claude Code, Codex CLI, or
Hermes CLI you intend to use; the project checks for them in `llm doctor`.

Then start the interactive tool:

```bash
llm
```

The first screen shows the active model separately from reachable services.
An Ollama daemon without a loaded model appears as `ready (idle)`, not active.
The menu always defaults to running a model; browsing models is second and
opening an agent is third.

The menu also includes stopping the active model and runtime diagnostics. If
llama.cpp already occupies port 8080, `llm start` offers to replace it.
Only one inference engine runs at a time: switching between llama.cpp and
Ollama stops the previous engine automatically.

Typical two-terminal workflow:

```bash
# Terminal 1
source .venv/bin/activate
llm start

# Terminal 2, from any project directory
claude-local
# or
codex-local
# or
hermes-local
```

The `*-local` commands preserve the directory where they are invoked and use
the active backend automatically.

## Model Inventory

The CLI works with any compatible GGUF model. The models mentioned in these
docs are examples used to validate the workflow on the reference laptop; users
should choose a model that fits their own hardware and quality requirements.

```bash
llm models
llm models --sort name
llm models --json
```

Model listings show installed sizes and sort smallest-first automatically.
`llm start` also displays sizes in its model picker.

Do not put weights in this repository. The default storage layout is:

```text
~/LLM/
  models/        # shared GGUF files
  llama.cpp/     # engine source and build
  ollama/        # Ollama state and model links
  .venv/         # managed Python environment
  run/           # logs and runtime state
```

Set `LLM_ROOT` or individual paths in `.env` to relocate them. See
[`docs/backends.md`](docs/backends.md).

## Context

The context window belongs to the running backend. Hermes and the other agent
launchers read the live server value; they should not carry a duplicate
hard-coded context setting. The launcher stops if it finds a stale Hermes
context pin that conflicts with the server.

For llama.cpp, the launch menu offers model-appropriate context sizes and
allows a custom value. Higher context consumes more VRAM or system RAM. See
[`docs/context-memory.md`](docs/context-memory.md).

## Documentation

| Document | Contents |
|---|---|
| [`docs/cli.md`](docs/cli.md) | `llm` commands and interactive workflow |
| [`docs/agents.md`](docs/agents.md) | Claude Code, Codex CLI, and Hermes Agent |
| [`docs/backends.md`](docs/backends.md) | llama.cpp, Ollama, storage, and lifecycle |
| [`docs/models.md`](docs/models.md) | Tested models and recommendations |
| [`docs/context-memory.md`](docs/context-memory.md) | Context windows and KV cache |
| [`docs/troubleshooting.md`](docs/troubleshooting.md) | Common failures and diagnosis |

Screenshots and media are intentionally omitted until the CLI presentation is
stable.
