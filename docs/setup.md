# Setup

English | [简体中文](setup.zh-CN.md)

This project is a locally deployable LLM agent workspace with flexible
deployment options: native host or portable drive.

Both modes use the same base layout: clone this repo as `local-llm-agent` next
to `llama-cpp/` and `Ollama/`. The same layout works for tiny CPU/SBC machines,
ordinary laptops, small GPUs, and high-end desktop GPUs; model size and context
settings are the parts that change.

```text
<parent>/
  local-llm-agent/
  llama-cpp/
  Ollama/
```

## Guided Setup

For a native host setup, use the setup flow below.

Check prerequisites and path resolution:

```bash
./scripts/setup/check-prereqs.sh
```

Build llama.cpp:

```bash
./scripts/setup/build-llama-cpp.sh --dry-run
./scripts/setup/build-llama-cpp.sh
```

Install Ollama (binary + systemd service):

```bash
./scripts/setup/install-ollama.sh --dry-run
./scripts/setup/install-ollama.sh
```

If you cannot use the script (e.g. Windows), install manually:
`curl -fsSL https://ollama.com/install.sh | sh` or download from https://ollama.com/download.

Configure Ollama's systemd override:

```bash
./scripts/setup/configure-ollama.sh --dry-run
./scripts/setup/configure-ollama.sh
sudo systemctl start ollama
```

If Ollama fails with `mkdir /home/...: permission denied`, your home directory
is not traversable by the `ollama` service user. Fix with:

```bash
chmod o+x ~
sudo systemctl start ollama
```

Install Cline's manual llama.cpp service:

```bash
./scripts/setup/install-llama-cline-service.sh --dry-run
./scripts/setup/install-llama-cline-service.sh
sudo systemctl start llama-cline
```

`llama-cline` is intentionally disabled for autostart. Start and stop it manually.

For a portable drive, skip system service setup unless you explicitly want a
host-specific service. Run the short-command installer once on each host where
the drive is plugged in, then start the portable server:

```bash
./scripts/setup/install-portable-ollama-command.sh
portable-ollama serve
```

The installer creates a symlink in `~/.local/bin`. If the shell cannot find
`portable-ollama`, add `~/.local/bin` to `PATH` on that host and open a new
terminal.

## Path Defaults

All scripts source `scripts/common/env.sh`.

| Variable | Default |
|---|---|
| `LOCAL_LLM_AGENT_ROOT` | repo root |
| `LLAMA_CPP_ROOT` | `$LOCAL_LLM_AGENT_ROOT/../llama-cpp` |
| `OLLAMA_ROOT` | `$LOCAL_LLM_AGENT_ROOT/../Ollama` |
| `OLLAMA_MODELS` | `$OLLAMA_ROOT/models/llm` |
| `LLM_MODELS_DIR` | `$LOCAL_LLM_AGENT_ROOT/models` |
| `LLAMA_CPP_BIN` | `$LLAMA_CPP_ROOT/build/bin/llama-cli` |
| `LLAMA_SERVER_BIN` | `$LLAMA_CPP_ROOT/build/bin/llama-server` |
| `SERVICE_USER` | user running the service installer |

Override any of these when your folders live elsewhere.

## Directory Layout

```text
local-llm-agent/
  .local/                 # local agent runtime state, venvs, and caches
  models/                 # local GGUF files, ignored by Git
  modelfiles/             # lightweight Ollama Modelfiles
  scripts/common/         # env and status helpers
  scripts/llama-cpp/      # llama.cpp wrappers
  scripts/ollama/         # Ollama sharing/maintenance helpers
  scripts/setup/          # guided setup scripts
  systemd/                # service templates
  tuning/                 # personality builder and comparison tools
  docs/                   # portable docs
```

Important docs:

- [`context-memory.md`](context-memory.md) explains context windows, KV cache, and durable project memory.
- [`models.md`](models.md) explains what model families are useful for.
- [`hardware-matching.md`](hardware-matching.md) matches model choices to hardware tiers.
- [`portable-llm-launcher.md`](portable-llm-launcher.md) explains running Ollama from a portable drive.
- [`cline.md`](cline.md) covers Cline with llama.cpp or Ollama.
- [`copilot.md`](copilot.md) covers Copilot Chat/CLI with Ollama.

## Services

Ollama can use `ollama.service`, with `OLLAMA_MODELS` configured to the path above.
This is the native host service path.

For a portable drive, prefer the Portable LLM Launcher instead of a service:

```bash
portable-ollama serve
```

`portable-ollama` uses the host-installed `ollama` command, the repo's sibling
`Ollama/models/llm` model store, and `127.0.0.1:14514`. Set
`OLLAMA_BIN=/path/to/ollama` if you need a specific executable.

`llama-cline.service` is generated from `systemd/llama-cline.service.in`. The installer fills in the current repo path and service user, installs to `/etc/systemd/system/llama-cline.service`, reloads systemd, and keeps the unit disabled.

## Model Sharing

The intended storage pattern is:

```text
models/<name>.gguf                        # real GGUF bytes
$OLLAMA_MODELS/blobs/sha256-<digest>      # symlink to the GGUF
```

llama.cpp opens `models/*.gguf` directly. Ollama opens its CAS path and follows the symlink. The helper scripts in `scripts/ollama/` maintain that relationship.

## Requirements

Minimum useful tools:

- `git`
- `cmake`
- C/C++ compiler
- `python3`
- `curl`
- Ollama, if using Ollama workflows
- systemd, if using service installers
- NVIDIA driver/CUDA-capable GPU for GPU offload, or a CPU-only llama.cpp build with adjusted flags
