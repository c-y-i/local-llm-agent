# Setup

English | [简体中文](setup.zh-CN.md)

This project is a locally deployable LLM agent workspace with flexible
deployment options: native host or portable drive. The Git repository remains
lightweight; all model, engine, cache, environment, and runtime data lives
under `LLM_ROOT`.

```text
~/LLM/                        # LLM_ROOT
  models/
    strata/
  ollama/
  llama.cpp/
  huggingface/
  strata/
  .venv/
  run/

~/Projects/local-llm-agent/   # this repository
```

The default can be changed in `.env`:

```bash
cp .env.example .env
# edit LLM_ROOT or individual path overrides
```

## Guided Setup

For a native host setup, use the setup flow below.

Check prerequisites and path resolution:

```bash
./scripts/setup/check-prereqs.sh
```

Install the CLI:

```bash
./scripts/setup/install-llm.sh
llm doctor
```

Build llama.cpp:

```bash
./scripts/setup/build-llama-cpp.sh --dry-run
./scripts/setup/build-llama-cpp.sh
```

The builder enables `GGML_CUDA` automatically when `nvcc` or
`/usr/local/cuda` is present. Force CPU-only or require CUDA explicitly:

```bash
LLAMA_CUDA=OFF ./scripts/setup/build-llama-cpp.sh
LLAMA_CUDA=ON  ./scripts/setup/build-llama-cpp.sh
```

The existing build directory is reused, so remove or use a separate
`LLAMA_CPP_ROOT` when switching between CPU-only and CUDA builds.

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
| `LLM_ROOT` | `$HOME/LLM` |
| `LLAMA_CPP_ROOT` | `$LLM_ROOT/llama.cpp` |
| `OLLAMA_ROOT` | `$LLM_ROOT/ollama` |
| `OLLAMA_MODELS` | `$OLLAMA_ROOT/models/llm` |
| `LLM_MODELS_DIR` | `$LLM_ROOT/models` |
| `HF_HOME` | `$LLM_ROOT/huggingface` |
| `STRATA_HOME` | `$LLM_ROOT/strata` |
| `STRATA_MODELS_DIR` | `$LLM_ROOT/models/strata` |
| `LLM_VENV_DIR` | `$LLM_ROOT/.venv` |
| `LLM_RUN_DIR` | `$LLM_ROOT/run` |
| `LLAMA_CPP_BIN` | `$LLAMA_CPP_ROOT/build/bin/llama-cli` |
| `LLAMA_SERVER_BIN` | `$LLAMA_CPP_ROOT/build/bin/llama-server` |
| `LLAMA_CPP_BASE_URL` | `http://127.0.0.1:8080` |
| `VLLM_BIN` | `vllm` on `PATH` |
| `VLLM_BASE_URL` | `http://127.0.0.1:8000` |
| `STRATA_BIN` | `strata` on `PATH` |
| `STRATA_BASE_URL` | `http://127.0.0.1:8082` |
| `SERVICE_USER` | user running the service installer |

Override any of these when your folders live elsewhere.

## Directory Layout

```text
local-llm-agent/
  .env                    # local path config, ignored by Git
  .env.example            # portable path template
  modelfiles/             # lightweight Ollama Modelfiles
  scripts/common/         # env and status helpers
  scripts/claude/         # backend-neutral Claude Code launcher
  scripts/llama-cpp/      # llama.cpp wrappers
  scripts/ollama/         # Ollama sharing/maintenance helpers
  scripts/strata/         # Strata launcher
  scripts/vllm/           # vLLM launcher
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
- [`usage-vllm.md`](usage-vllm.md) covers vLLM and tool-call parser setup.
- [`usage-strata.md`](usage-strata.md) covers Strata model planning and serving.
- [`cli.md`](cli.md) is the `llm` command reference.
- [`cline.md`](cline.md) covers Cline with llama.cpp or Ollama.
- [`copilot.md`](copilot.md) covers Copilot Chat/CLI with Ollama.

## Services

Ollama can use `ollama.service`, with `OLLAMA_MODELS` configured to the path above.
This is the native host service path.

For a portable drive, prefer the Portable LLM Launcher instead of a service:

```bash
portable-ollama serve
```

`portable-ollama` uses the host-installed `ollama` command, the configured
`OLLAMA_MODELS` model store, and `127.0.0.1:14514`. Set
`OLLAMA_BIN=/path/to/ollama` if you need a specific executable.

`llama-cline.service` is generated from `systemd/llama-cline.service.in`. The installer fills in the current repo path and service user, installs to `/etc/systemd/system/llama-cline.service`, reloads systemd, and keeps the unit disabled.

## Model Sharing

The intended storage pattern is:

```text
$LLM_MODELS_DIR/<name>.gguf               # real GGUF bytes
$OLLAMA_MODELS/blobs/sha256-<digest>      # symlink to the GGUF
```

llama.cpp opens `$LLM_MODELS_DIR/*.gguf`. Ollama opens its CAS path and follows
the symlink. The helper scripts in `scripts/ollama/` maintain that
relationship.

## Requirements

Minimum useful tools:

- `git`
- `cmake`
- C/C++ compiler
- `python3`
- `curl`
- Ollama, if using Ollama workflows
- vLLM, if using vLLM workflows
- Strata, if using Strata workflows
- Claude Code CLI, if using the Claude Code launcher
- Codex CLI, if using the Codex launcher
- Hermes Agent, if using the Hermes launcher
- systemd, if using service installers
- NVIDIA driver/CUDA-capable GPU for GPU offload, or a CPU-only llama.cpp build with adjusted flags
