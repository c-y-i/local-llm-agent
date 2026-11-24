# local-llm-agent

English | [简体中文](README.zh-CN.md)

Run local coding models on your own hardware and connect them to Claude Code,
Codex CLI, or Hermes Agent. The repository contains code, documentation, and
small configuration files; model weights and runtime state live outside Git.

## Reference Setup And Tested Agents

The current benchmark machine is an Intel Core i7-12700F with 32 GB RAM and
an NVIDIA RTX 3060 with 12 GB VRAM. The workflow is tested end to end there
with:

- Claude Code
- Codex CLI
- Hermes Agent

The shared tested backend is llama.cpp. The main daily model is Qwen3.5-4B,
while Qwen3.5-14B, DeepSeek-R1-Distill-Qwen-14B, and larger sparse Ollama
models are available for higher-quality or reasoning work. These models are
examples for this hardware tier, not requirements.

## Current Scope

| Component | Status | Endpoint |
|---|---|---|
| llama.cpp | Primary local backend | `http://127.0.0.1:8080` |
| Ollama | Secondary backend and model store | `http://127.0.0.1:11434` |
| Claude Code | Tested | llama.cpp native, Ollama through proxy |
| Codex CLI | Tested | llama.cpp Responses provider |
| Hermes Agent | Tested | OpenAI-compatible endpoint |
| Windows 10/11 x64 | Supported | llama.cpp, Ollama, and all agents natively |
| vLLM | Deferred | Not part of the current hardware workflow |
| Strata | Deferred | Not part of the current hardware workflow |

Documentation and screenshots for older Cline, Copilot, control-panel,
portable-launcher, vLLM, and Strata workflows were removed for now. The docs
now describe the tested local-agent path only.

## Install

```bash
./scripts/setup/install-llm.sh
llm --version
```

The `llm` command and the direct agent commands activate the managed Python
environment automatically.

Windows users can use the native PowerShell workflow:

```powershell
.\scripts\setup\install-llm.ps1 -AddToPath
.\llm.cmd doctor
```

See [`docs/windows.md`](docs/windows.md).

## Quick Start

For a new installation, start with
[`docs/agent-setup.md`](docs/agent-setup.md): inspect the hardware, ask what
kind of model the user wants, and install only the selected model. The Qwen
download below is an example, not a default.

Check prerequisites and build llama.cpp:

```bash
./scripts/setup/check-prereqs.sh
llm setup

curl -fL --retry 5 -C - \
  -o ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf.part \
  https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/main/Qwen3.5-4B-Q4_K_M.gguf
mv ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf.part \
  ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf
```

The example download is about 2.6 GB. Qwen3.5-2B is a smaller alternative, and
Gemma is another option for general-purpose work; see
[`docs/models.md`](docs/models.md). Do not assume either example matches the
user's hardware or goals. Install only the Claude Code, Codex CLI, or Hermes
CLI you intend to use; `llm doctor` checks for them.

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
docs are examples used to validate the workflow on the current benchmark
machine; users should choose a model that fits their own hardware and quality
requirements.

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
| [`docs/agent-setup.md`](docs/agent-setup.md) | Hardware assessment, model choice, and end-to-end agent onboarding |
| [`docs/cli.md`](docs/cli.md) | `llm` commands and interactive workflow |
| [`docs/agents.md`](docs/agents.md) | Claude Code, Codex CLI, and Hermes Agent |
| [`docs/backends.md`](docs/backends.md) | llama.cpp, Ollama, storage, and lifecycle |
| [`docs/models.md`](docs/models.md) | Tested models and recommendations |
| [`docs/context-memory.md`](docs/context-memory.md) | Context windows and KV cache |
| [`docs/windows.md`](docs/windows.md) | Native Windows setup, PowerShell scripts, and `.cmd` launchers |
| [`docs/troubleshooting.md`](docs/troubleshooting.md) | Common failures and diagnosis |

Screenshots and media are intentionally omitted until the CLI presentation is
stable.
