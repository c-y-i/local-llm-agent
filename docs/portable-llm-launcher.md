# Portable LLM Launcher

The Portable LLM Launcher carries the Ollama model store and optional
OS-specific Ollama binaries on a removable drive. It should not carry a system
service. Services are host-specific; a foreground launcher is easier to move
between computers.

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
copy a matching binary into `bin/ollama/<os>-<arch>/` or install Ollama
normally and use the same portable model store.

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

Linux or macOS:

```bash
cd /path/to/portable-drive/local-llm-agent
./scripts/ollama/portable-llm-launcher.sh
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

In another terminal, use the same `OLLAMA_HOST`:

```bash
OLLAMA_HOST=127.0.0.1:11434 ollama list
OLLAMA_HOST=127.0.0.1:11434 ollama run qwen3:4b
```

If the host already has Ollama running on `11434`, use a different port:

```bash
OLLAMA_HOST=127.0.0.1:11435 ./scripts/ollama/portable-llm-launcher.sh
```

On Windows PowerShell:

```powershell
$env:OLLAMA_HOST="127.0.0.1:11435"
.\scripts\ollama\portable-llm-launcher.ps1
```

Then query that port:

```bash
OLLAMA_HOST=127.0.0.1:11435 ollama list
OLLAMA_HOST=127.0.0.1:11435 ollama run qwen3:30b
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
