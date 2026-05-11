# Portable LLM Launcher

English | [简体中文](portable-llm-launcher.zh-CN.md)

This project supports portable drive deployment as an optional target. The same
repo layout can run on the native host with `./scripts/ollama/serve.sh`, or
move between hosts with the Ollama model store and optional OS-specific Ollama
binaries.

The portable drive should not carry a system service. Services are
host-specific; a foreground launcher is easier to move between computers.

## What Is Portable

```text
<portable-drive>/
  local-llm-agent/
  Ollama/models/llm/
  bin/ollama/linux-amd64/ollama
  bin/ollama/darwin-arm64/ollama
  bin/ollama/windows-amd64/ollama.exe
```

- `Ollama/models/llm/` is the portable model library.
- `bin/ollama/<os>-<arch>/ollama[.exe]` is an optional portable binary.
- `local-llm-agent/scripts/ollama/portable-llm-launcher.*` starts Ollama with
  the portable model store.

The bundled binary only works on matching operating systems and CPU
architectures. For example, a Linux x86_64 binary works on most Linux x86_64
desktops and laptops, but not Windows, macOS, or ARM systems. On those hosts,
copy a matching binary into `bin/ollama/<os>-<arch>/` or install Ollama on the
host and use the same portable model store.

Supported launcher targets:

| Host | Launcher | Binary slot |
|---|---|---|
| Linux x86_64 | `portable-llm-launcher.sh` | `bin/ollama/linux-amd64/ollama` |
| Linux ARM64 | `portable-llm-launcher.sh` | `bin/ollama/linux-arm64/ollama` |
| macOS Intel | `portable-llm-launcher.sh` | `bin/ollama/darwin-amd64/ollama` |
| macOS Apple Silicon | `portable-llm-launcher.sh` | `bin/ollama/darwin-arm64/ollama` |
| Windows x86_64 | `portable-llm-launcher.cmd` or `.ps1` | `bin/ollama/windows-amd64/ollama.exe` |
| Windows ARM64 | `portable-llm-launcher.cmd` or `.ps1` | `bin/ollama/windows-arm64/ollama.exe` |

## Add A Portable Binary

On a machine where `ollama` already works:

```bash
./scripts/ollama/install-portable-llm-binary.sh
```

Or copy a specific binary:

```bash
./scripts/ollama/install-portable-llm-binary.sh --from /usr/local/bin/ollama
```

To stage a binary for another OS after obtaining that binary:

```bash
./scripts/ollama/install-portable-llm-binary.sh --from ./ollama.exe --os windows --arch amd64
```

## Run The Launcher

This section is only for the portable drive workflow. For native host use,
use [`usage-ollama.md`](usage-ollama.md) and
`./scripts/ollama/serve.sh` instead.

Daily portable use is two commands:

```bash
# Terminal 1: keep the portable server running.
llm-portable

# Terminal 2: talk to that portable server.
llm-ollama list
llm-ollama run qwen3:4b
```

### Command Flow

Run these from the portable drive repo:

```bash
cd /path/to/portable-drive/local-llm-agent

# Optional: copy the host's Ollama binary onto the drive.
# This does not start Ollama.
./scripts/ollama/install-portable-llm-binary.sh

# Install the short shell commands once.
./scripts/setup/install-llm-portable-command.sh
source ~/.bashrc

# Start the portable Ollama server on 127.0.0.1:14514.
llm-portable
```

In another terminal:

```bash
llm-ollama list
llm-ollama run qwen3:4b
```

Script roles:

| Script | What it does | Starts Ollama? |
|---|---|---|
| `install-portable-llm-binary.sh` | Copies an Ollama executable into `../bin/ollama/<os>-<arch>/` | No |
| `install-llm-portable-command.sh` | Adds or updates `llm-portable` and `llm-ollama` in `~/.bashrc` | No |
| `llm-portable.sh` / `llm-portable` | Starts the portable Ollama server with `OLLAMA_HOST=127.0.0.1:14514` | Yes |
| `llm-ollama.sh` / `llm-ollama` | Runs Ollama CLI commands with `OLLAMA_HOST=127.0.0.1:14514` | No |
| `portable-llm-launcher.sh` | Low-level launcher; defaults to `11434` unless `OLLAMA_HOST` is set | Yes |

### Command Notes

`install-llm-portable-command.sh` adds or updates `llm-portable` and
`llm-ollama` functions in `~/.bashrc`. They use the current repo path, so run
the installer from the drive after cloning or pulling this repo there.

If the drive is unplugged, the shell function remains in `~/.bashrc` but does
nothing until called. If you call it while the drive is missing, it prints a
message telling you to plug the drive back in or rerun setup from the new mount
path.

To preview the shell function without editing `~/.bashrc`:

```bash
./scripts/setup/install-llm-portable-command.sh --dry-run
```

To remove the shell function:

```bash
./scripts/setup/install-llm-portable-command.sh --remove
source ~/.bashrc
```

You can also run the wrapper directly:

```bash
./scripts/ollama/llm-portable.sh
```

The setup script installs this shell function:

```bash
function llm-portable() {
  /path/to/portable-drive/local-llm-agent/scripts/ollama/llm-portable.sh "$@"
}

function llm-ollama() {
  /path/to/portable-drive/local-llm-agent/scripts/ollama/llm-ollama.sh "$@"
}
```

### Direct Launcher

Most users should use `llm-portable` and `llm-ollama`. The underlying launcher
still defaults to `11434` unless `OLLAMA_HOST` is set:

```bash
OLLAMA_HOST=127.0.0.1:14514 ./scripts/ollama/portable-llm-launcher.sh
```

Windows Command Prompt:

```bat
cd /d X:\local-llm-agent
scripts\ollama\portable-llm-launcher.cmd
```

Windows PowerShell:

```powershell
cd X:\local-llm-agent
.\scripts\ollama\portable-llm-launcher.ps1
```

For Windows or any direct launcher use, query the same `OLLAMA_HOST`.
PowerShell:

```powershell
$env:OLLAMA_HOST="127.0.0.1:11434"
ollama list
ollama run qwen3:4b
```

Bash:

```bash
OLLAMA_HOST=127.0.0.1:11434 ollama list
OLLAMA_HOST=127.0.0.1:11434 ollama run qwen3:4b
```

If the host already has Ollama running on `11434`, use a different port:

```bash
OLLAMA_HOST=127.0.0.1:14514 ./scripts/ollama/portable-llm-launcher.sh
```

On Windows PowerShell:

```powershell
$env:OLLAMA_HOST="127.0.0.1:14514"
.\scripts\ollama\portable-llm-launcher.ps1
```

On Linux/macOS with the helper installed, query that port with:

```bash
llm-ollama list
llm-ollama run qwen3:30b
```

Without the helper, keep using the same host value:

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
