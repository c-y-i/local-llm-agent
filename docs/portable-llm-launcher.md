# Portable LLM Launcher

English | [简体中文](portable-llm-launcher.zh-CN.md)

This project supports portable drive deployment as an optional target. The same
repo layout can run on the native host with `./scripts/ollama/serve.sh`, or move
between hosts with the Ollama model store.

The portable drive should not carry a system service. Services are
host-specific; a foreground launcher is easier to move between computers.

## What Is Portable

```text
<portable-drive>/
  local-llm-agent/
  Ollama/models/llm/
```

- `Ollama/models/llm/` is the portable model library.
- `local-llm-agent/scripts/ollama/portable-llm-launcher.*` starts Ollama with
  the portable model store.
- The launcher uses the host's `ollama` command. Set
  `OLLAMA_BIN=/path/to/ollama` when you need a specific executable.

## Run The Launcher

This section is only for the portable drive workflow. For native host use,
use [`usage-ollama.md`](usage-ollama.md) and
`./scripts/ollama/serve.sh` instead.

Run these from the portable drive repo:

```bash
cd /path/to/portable-drive/local-llm-agent

# Install the short command once on this host.
./scripts/setup/install-portable-ollama-command.sh

# Terminal 1: keep the portable server running.
portable-ollama serve
```

In another terminal:

```bash
portable-ollama list
portable-ollama run qwen3:4b
```

Script roles:

| Script | What it does | Starts Ollama? |
|---|---|---|
| `portable-ollama` | Runs Ollama commands against the portable store; `serve` starts the portable server | Only with `serve` |
| `install-portable-ollama-command.sh` | Symlinks `portable-ollama` into `~/.local/bin` | No |
| `portable-llm-launcher.sh` | Starts Ollama with this repo's sibling `Ollama/models/llm` store | Yes |
| `portable-llm-launcher.ps1` / `.cmd` | Windows launcher for the same portable model-store layout | Yes |

### Direct Launcher

The launcher defaults to `127.0.0.1:11434` unless `OLLAMA_HOST` is set. If the
host already has Ollama running on `11434`, use a different port:

```bash
OLLAMA_HOST=127.0.0.1:14514 ./scripts/ollama/portable-llm-launcher.sh
```

Windows Command Prompt:

```bat
cd /d X:\local-llm-agent
set OLLAMA_HOST=127.0.0.1:14514
scripts\ollama\portable-llm-launcher.cmd
```

Windows PowerShell:

```powershell
cd X:\local-llm-agent
$env:OLLAMA_HOST="127.0.0.1:14514"
.\scripts\ollama\portable-llm-launcher.ps1
```

For Windows or any direct launcher use, query the same `OLLAMA_HOST`.
PowerShell:

```powershell
$env:OLLAMA_HOST="127.0.0.1:14514"
ollama list
ollama run qwen3:4b
```

Bash:

```bash
OLLAMA_HOST=127.0.0.1:14514 ollama list
OLLAMA_HOST=127.0.0.1:14514 ollama run qwen3:30b
```

## Model Choice

Use small models on unknown or weak machines:

```bash
ollama run qwen3:4b
ollama run llama3.2:3b
ollama run qwen2.5-coder:3b
```

Use larger models only on machines with enough RAM or VRAM:

```bash
ollama run qwen3:14b
ollama run qwen3:30b
ollama run gemma3:12b
```

See [`hardware-matching.md`](hardware-matching.md) for hardware tiers.
