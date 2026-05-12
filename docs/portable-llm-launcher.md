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

## Prerequisites

The launcher uses the **host machine's** `ollama` binary — it does not bundle
one. Install Ollama on each new host before running the launcher. See
[`setup.md`](setup.md#install-ollama) for instructions.

## Run The Launcher

This section is only for the portable drive workflow. For native host use,
use [`usage-ollama.md`](usage-ollama.md) and
`./scripts/ollama/serve.sh` instead.

Run these from the portable drive repo:

```bash
cd /path/to/portable-drive/local-llm-agent

# Run once on each host where this drive is plugged in.
./scripts/setup/install-portable-ollama-command.sh

# Terminal 1: keep the portable server running.
portable-ollama serve
```

The installer creates a symlink in `~/.local/bin`. If the shell cannot find
`portable-ollama`, add `~/.local/bin` to `PATH` on that host and open a new
terminal.

In another terminal:

```bash
portable-ollama list
portable-ollama run <model>
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
ollama run <model>
```

Bash:

```bash
OLLAMA_HOST=127.0.0.1:14514 ollama list
OLLAMA_HOST=127.0.0.1:14514 ollama run <model>
```

## Model Choice

```bash
ollama run <model>
```

See [`hardware-matching.md`](hardware-matching.md) for hardware tier recommendations.
