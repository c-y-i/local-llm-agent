# Portable SSD Ollama

The SSD can carry both the Ollama model store and, for compatible machines, an
Ollama executable. It should not carry a system service. Services are
host-specific; a foreground server is easier to move between computers.

## What Is Portable

```text
128ssd/
  local-llm-agent/
  Ollama/models/llm/
  bin/ollama/linux-amd64/ollama
```

- `Ollama/models/llm/` is the portable model library.
- `bin/ollama/<os>-<arch>/ollama` is an optional portable binary.
- `local-llm-agent/scripts/ollama/portable-serve.sh` starts Ollama with the
  SSD model store.

The bundled binary only works on matching operating systems and CPU
architectures. A Linux x86_64 binary works on most Linux x86_64 desktops and
laptops, but not Windows, macOS, or ARM systems. On those hosts, install Ollama
normally and use the same SSD model store.

## Add A Portable Binary

On a machine where `ollama` already works:

```bash
./scripts/ollama/install-portable-ollama.sh
```

Or copy a specific binary:

```bash
./scripts/ollama/install-portable-ollama.sh --from /usr/local/bin/ollama
```

## Run From The SSD

After plugging in the SSD:

```bash
cd /media/$USER/128ssd/local-llm-agent
./scripts/ollama/portable-serve.sh
```

In another terminal:

```bash
OLLAMA_HOST=127.0.0.1:11434 ollama list
OLLAMA_HOST=127.0.0.1:11434 ollama run qwen3:4b
```

If the host already has Ollama running on `11434`, use a different port:

```bash
OLLAMA_HOST=127.0.0.1:11435 ./scripts/ollama/portable-serve.sh
```

Then use:

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
