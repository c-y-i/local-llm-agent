# Setup

This project is designed to be cloned as `local-llm-agent` next to `llama-cpp/` and `Ollama/`. The same layout works for tiny CPU/SBC machines, ordinary laptops, small GPUs, and high-end desktop GPUs; model size and context settings are the parts that change.

```text
<parent>/
  local-llm-agent/
  llama-cpp/
  Ollama/
```

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

## Guided Setup

Check prerequisites and path resolution:

```bash
./scripts/setup/check-prereqs.sh
```

Build llama.cpp:

```bash
./scripts/setup/build-llama-cpp.sh --dry-run
./scripts/setup/build-llama-cpp.sh
```

Configure Ollama's systemd override:

```bash
./scripts/setup/configure-ollama.sh --dry-run
./scripts/setup/configure-ollama.sh
sudo systemctl start ollama
```

Install Cline's manual llama.cpp service:

```bash
./scripts/setup/install-llama-cline-service.sh --dry-run
./scripts/setup/install-llama-cline-service.sh
sudo systemctl start llama-cline
```

`llama-cline` is intentionally disabled for autostart. Start and stop it manually.

## Directory Layout

```text
local-llm-agent/
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
- [`portable-llm-launcher.md`](portable-llm-launcher.md) explains running Ollama from a removable drive.
- [`cline.md`](cline.md) covers Cline with llama.cpp or Ollama.
- [`copilot.md`](copilot.md) covers Copilot Chat/CLI with Ollama.

## Services

Ollama uses its normal `ollama.service`, with `OLLAMA_MODELS` configured to the path above.

For removable-drive use, prefer the Portable LLM Launcher instead of a service:

```bash
./scripts/ollama/portable-llm-launcher.sh
```

The launcher can use either a host-installed `ollama` or a compatible binary
copied onto the removable drive with `./scripts/ollama/install-portable-llm-binary.sh`.

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
