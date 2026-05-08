# local-llm-agent

English | [简体中文](README.zh-CN.md)

Locally deployable LLM sandbox: runs llama.cpp, Ollama, model files, service scripts, and a web dashboard all from one directory. Plug it into Cline, Claude Code, or Copilot.

## Quick Start

```bash
./scripts/setup/check-prereqs.sh
./scripts/ollama/serve.sh
python3 control_panel.py   # http://localhost:8766
```

## Dashboard

`monitor.py` (read-only, port 8765) and `control_panel.py` (full controls, port 8766) are single-file Python dashboards that require nothing beyond stdlib.

<!-- Add control panel screenshot here -->

**What the dashboard shows:**

| Card | Contents |
|---|---|
| Services | ollama, llama-cline, litellm-proxy — start / stop / restart |
| GPU | VRAM usage, utilization, temperature |
| System | CPU model, cores, RAM meter |
| Storage | Root disk + Ollama models directory (highlights >85% full) |
| Models | Full Ollama model list with load / unload controls |

**Setup flow:** the control panel detects when Ollama isn't running (shows a one-click start banner) and when no models are pulled (shows a curated pull list: qwen3:4b, qwen2.5-coder:3b, llama3.2:1b). Once a model is pulled, the panel transitions to the normal view automatically.

```bash
python3 monitor.py         # read-only  — http://localhost:8765
python3 control_panel.py   # controls   — http://localhost:8766
LLM_DASHBOARD_PORT=9000 python3 monitor.py   # override port
```

Controls only accept localhost connections and run as the current user.

## Hardware Model Matching

| Hardware | General chat | Coding / Cline | Context |
|---|---|---|---:|
| SBC: RPi / Orange Pi, 8 GB | `llama3.2:1b` | `qwen2.5-coder:0.5b` | 2048 |
| Mini PC: N100/N305, 16 GB | `llama3.2:1b` | `qwen2.5-coder:1.5b` | 4096 |
| RTX 3050 laptop, 6 GB VRAM | `qwen3:4b` | `gemma4:e4b`, `qwen2.5-coder:3b` | 4096–8192 |
| RTX 3060, 12 GB | `qwen3:8b` | `qwen2.5-coder:7b` | 8192–16384 |
| RTX 4080 / 4080 Super | `mistral-nemo:12b` | `qwen2.5-coder:14b` | 16384–32768 |
| RTX 4090 / 5090 | `qwen3:30b`, `gpt-oss:20b` | `qwen2.5-coder:32b` | 32768+ |
| High-memory Mac | 7B–32B Q4 | `qwen2.5-coder` Q4 | 8192–32768 |

Full list and traps: [`docs/hardware-matching.md`](docs/hardware-matching.md)

## Agents

### Cline

Connect to llama.cpp for direct GGUF control:

| Field | Value |
|---|---|
| API Provider | `OpenAI Compatible` |
| Base URL | `http://127.0.0.1:8080/v1` |
| API Key | `114514` |
| Model ID / Context | printed by `./scripts/llama-cpp/cline-server.sh` |

Or connect directly to Ollama (`API Provider: Ollama`, Base URL `http://127.0.0.1:11434`).

<img src="docs/cline_demo.png" alt="Cline running with a local Ollama model" width="720">

Full guide: [`docs/cline.md`](docs/cline.md)

### Claude Code

```bash
./scripts/ollama/serve.sh
sudo systemctl start litellm-proxy
claude-local   # model picker — loaded models shown first, marked RUNNING
```

Full guides: [`docs/claude-local.md`](docs/claude-local.md), [`docs/claude-code.md`](docs/claude-code.md), [`docs/claude-proxy.md`](docs/claude-proxy.md)

### Copilot

```bash
./scripts/ollama/serve.sh
ollama pull qwen2.5-coder:7b
```

Then select the local model in VS Code Copilot Chat. Full guide: [`docs/copilot.md`](docs/copilot.md)

## Layout

```text
<parent>/
  local-llm-agent/   # this repo
  llama-cpp/         # llama.cpp source/build
  Ollama/            # Ollama model store
```

Every path is overridable via env vars. Large model files (GGUF, Ollama blobs) are gitignored. See [`docs/setup.md`](docs/setup.md) for the full env var reference and service setup.

## Docs

| File | What it covers |
|---|---|
| [`docs/setup.md`](docs/setup.md) | Portable layout, env vars, services, setup flow |
| [`docs/usage-llama-cpp.md`](docs/usage-llama-cpp.md) | llama.cpp CLI/server usage |
| [`docs/usage-ollama.md`](docs/usage-ollama.md) | Ollama service and API usage |
| [`docs/cline.md`](docs/cline.md) | Cline integration and troubleshooting |
| [`docs/copilot.md`](docs/copilot.md) | Copilot Chat/CLI with Ollama |
| [`docs/claude-local.md`](docs/claude-local.md) | `claude-local` launcher and model picker |
| [`docs/claude-code.md`](docs/claude-code.md) | Claude Code CLI with Ollama |
| [`docs/claude-proxy.md`](docs/claude-proxy.md) | Local Anthropic proxy internals |
| [`docs/context-memory.md`](docs/context-memory.md) | Context windows, KV cache, persistent memory |
| [`docs/models.md`](docs/models.md) | Model families and what they do |
| [`docs/hardware-matching.md`](docs/hardware-matching.md) | Hardware tiers → model choices |
| [`docs/maintenance.md`](docs/maintenance.md) | Add / remove / audit / update models |
| [`docs/tuning.md`](docs/tuning.md) | Parameters and Modelfile workflow |
