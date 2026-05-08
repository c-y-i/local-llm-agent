# local-llm-agent

English | [简体中文](README.zh-CN.md)

Locally deployable LLM sandbox: runs llama.cpp, Ollama, model files, service scripts, and a web dashboard all from one directory. Plug it into Cline, Claude Code, or Copilot.

## Quick Start

```bash
./scripts/setup/check-prereqs.sh
./scripts/ollama/serve.sh
python3 control_panel.py   # http://localhost:8766
```

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

<img src="docs/claude_local_menu.png" alt="claude-local model picker showing loaded Ollama models first" width="720">

Full guides: [`docs/claude-local.md`](docs/claude-local.md), [`docs/claude-code.md`](docs/claude-code.md), [`docs/claude-proxy.md`](docs/claude-proxy.md)

### Copilot

```bash
./scripts/ollama/serve.sh
ollama pull qwen2.5-coder:7b
```

Then select the local model in VS Code Copilot Chat.

<img src="docs/copilot_ollama.png" alt="VS Code Copilot Chat model picker showing local Ollama models" width="720">

Full guide: [`docs/copilot.md`](docs/copilot.md)

## Dashboard

`monitor.py` (read-only, port 8765) and `control_panel.py` (full controls, port 8766) are single-file Python dashboards that require nothing beyond stdlib.

<img src="docs/control_panel.png" alt="Local LLM Control Panel dashboard" width="720">

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
| [`docs/hardware-matching.md`](docs/hardware-matching.md) | Hardware tiers → model choices |
| [`docs/usage-llama-cpp.md`](docs/usage-llama-cpp.md) | llama.cpp CLI/server usage |
| [`docs/usage-ollama.md`](docs/usage-ollama.md) | Ollama service and API usage |
| [`docs/cline.md`](docs/cline.md) | Cline integration and troubleshooting |
| [`docs/copilot.md`](docs/copilot.md) | Copilot Chat/CLI with Ollama |
| [`docs/claude-local.md`](docs/claude-local.md) | `claude-local` launcher and model picker |
| [`docs/claude-code.md`](docs/claude-code.md) | Claude Code CLI with Ollama |
| [`docs/claude-proxy.md`](docs/claude-proxy.md) | Local Anthropic proxy internals |
| [`docs/context-memory.md`](docs/context-memory.md) | Context windows, KV cache, persistent memory |
| [`docs/models.md`](docs/models.md) | Model families and what they do |
| [`docs/maintenance.md`](docs/maintenance.md) | Add / remove / audit / update models |
| [`docs/tuning.md`](docs/tuning.md) | Parameters and Modelfile workflow |
