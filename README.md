# local-llm-agent

English | [简体中文](README.zh-CN.md)

`local-llm-agent` is a locally deployable LLM sandbox that can also plug into agent workflows. It keeps llama.cpp, Ollama, model files, Cline/Copilot setup, service scripts, and tuning notes together so you can run models on your own machine without turning the setup into a mystery box.

The default layout is three sibling folders:

```text
<parent>/
  local-llm-agent/   # this repo
  llama-cpp/         # llama.cpp source/build
  Ollama/            # Ollama model store
```

You can override every path with environment variables.

## Quick Start

```bash
./scripts/setup/check-prereqs.sh
./scripts/common/show-paths.sh
./scripts/setup/build-llama-cpp.sh
./scripts/ollama/serve.sh
./scripts/llama-cpp/cline-server.sh
```

`scripts/ollama/serve.sh` starts a foreground Ollama server with `OLLAMA_MODELS` pointed at this workspace's shared model store. Plain `ollama serve` uses Ollama's default store unless you export `OLLAMA_MODELS` yourself.

After quick start, `ollama list` should show local models and `ollama run <model>` should open a terminal chat:

![Terminal showing Ollama service status, model list, and an ollama run chat](docs/ollama_service.png)

For a manual `llama-cline` systemd service:

```bash
./scripts/setup/install-llama-cline-service.sh
sudo systemctl start llama-cline
```

`llama-cline` does not autostart. When you start it, it stops `ollama.service` first so both runtimes do not fight over the same GPU memory.

## Hardware Model Matching

| Example | General chat | Coding / Cline | Context |
|---|---|---|---:|
| Single Board Computer: Raspberry Pi / Orange Pi, 8 GB | `llama3.2:1b` | `qwen2.5-coder:0.5b` | 2048 |
| Used mini PC: Intel N100/N305, 16 GB | `llama3.2:1b` | `qwen2.5-coder:1.5b` | 4096 |
| Budget Cline GPU: RTX 3060 12 GB | `qwen3:8b` | `qwen2.5-coder:7b` | 8192-16384 |
| Strong gaming PC: RTX 4080 / 4080 Super | `mistral-nemo:12b` | `qwen2.5-coder:14b` | 16384-32768 |
| High-end single GPU: RTX 4090 / 5090 | `qwen3:30b`, `gpt-oss:20b` | `qwen2.5-coder:32b`, `qwen3-coder:30b` | 32768+ |
| High-memory Mac: Mac Studio / MacBook Pro | 7B-32B Q4 models | `qwen2.5-coder` family in Q4 | 8192-32768 |

See [`docs/hardware-matching.md`](docs/hardware-matching.md) for the full hardware list and the little traps worth knowing about.

## Editor / Agent Examples

Use Copilot Chat with Ollama when you want VS Code to use installed Ollama models:

```bash
./scripts/ollama/serve.sh
ollama pull qwen2.5-coder:7b
ollama launch vscode
```

In VS Code Copilot Chat, select a local Ollama model from the model picker. If you configure it manually, add Ollama as a language model provider and make sure the local model is visible.

![VS Code Language Models picker showing Ollama models](docs/copilot_ollama.png)

Use Cline with llama.cpp when you want direct control over GGUF files and context settings:

| Cline field | Value |
|---|---|
| API Provider | `OpenAI Compatible` |
| Base URL | `http://127.0.0.1:8080/v1` |
| API Key | `114514` |
| Model ID | model printed by `cline-server.sh` |
| Context Window Size | `Context` value printed by `cline-server.sh` |
| Temperature | `0.2` |
| Max Tokens | `1024` to `2048` |

Use Cline with Ollama when you want Cline to use an installed Ollama model directly:

| Cline field | Value |
|---|---|
| API Provider | `Ollama` |
| Base URL | `http://127.0.0.1:11434` |
| API Key | `114514` if Cline asks for one |
| Model ID | an installed Ollama tag, e.g. `qwen-coder-cline` |
| Context Window Size | model-specific, start with `4096` to `8192` |
| Temperature | `0.2` |
| Max Tokens | `1024` to `2048` |

If `models/qwen2.5-coder-3b.gguf` exists, the llama.cpp wrapper uses it by default.

See [`docs/cline.md`](docs/cline.md) for Cline details and [`docs/copilot.md`](docs/copilot.md) for Copilot + Ollama notes.

## Path Variables

| Variable | Default |
|---|---|
| `LOCAL_LLM_AGENT_ROOT` | this repo |
| `LLAMA_CPP_ROOT` | `../llama-cpp` |
| `OLLAMA_ROOT` | `../Ollama` |
| `OLLAMA_MODELS` | `$OLLAMA_ROOT/models/llm` |
| `LLM_MODELS_DIR` | `$LOCAL_LLM_AGENT_ROOT/models` |
| `LLAMA_CPP_BIN` | `$LLAMA_CPP_ROOT/build/bin/llama-cli` |
| `LLAMA_SERVER_BIN` | `$LLAMA_CPP_ROOT/build/bin/llama-server` |
| `SERVICE_USER` | current install user |

Example override:

```bash
LLAMA_CPP_ROOT="$HOME/src/llama.cpp" \
OLLAMA_ROOT="$HOME/.ollama-local" \
./scripts/llama-cpp/cline-server.sh
```

## Model Storage

Put local GGUF files here:

```text
models/
```

Large model files are ignored by `.gitignore`. Keep model catalogs and setup notes in docs, but do not commit GGUFs, Ollama blobs, caches, or machine-specific service state.

Ollama can share those files through CAS symlinks under `$OLLAMA_MODELS`. The helper scripts in `scripts/ollama/` handle pulling, importing, relinking, auditing, and removing shared models.

## Common Commands

```bash
./scripts/llama-cpp/llm-list.sh
./scripts/llama-cpp/llm-run.sh qwen3-4b
./scripts/llama-cpp/cline-status.sh
./scripts/ollama/serve.sh
./scripts/ollama/setup-small-models.sh
./scripts/ollama/check-symlinks.sh
sudo systemctl stop llama-cline
sudo systemctl stop ollama
```

## Docs

| File | What it covers |
|---|---|
| [`docs/setup.md`](docs/setup.md) | Portable layout, env vars, services, and setup flow |
| [`docs/usage-llama-cpp.md`](docs/usage-llama-cpp.md) | llama.cpp CLI/server usage |
| [`docs/usage-ollama.md`](docs/usage-ollama.md) | Ollama service and API usage |
| [`docs/cline.md`](docs/cline.md) | Cline integration and troubleshooting |
| [`docs/copilot.md`](docs/copilot.md) | Copilot Chat/CLI with Ollama |
| [`docs/context-memory.md`](docs/context-memory.md) | Context windows, KV cache, project rules, and persistent memory |
| [`docs/models.md`](docs/models.md) | What model families are and what they do |
| [`docs/hardware-matching.md`](docs/hardware-matching.md) | Matching hardware tiers to model choices |
| [`docs/maintenance.md`](docs/maintenance.md) | Add/remove/audit/update/troubleshoot tasks |
| [`docs/tuning.md`](docs/tuning.md) | Parameters and personality Modelfile workflow |

Keep local machine history in ignored files such as `.local/worklog.md`.
