# Using Ollama

Ollama is optional, but useful for pulling models, running non-Cline chats, and maintaining a shared model store.

## Manual Server

Recommended manual workflow:

```bash
./scripts/ollama/serve.sh
```

Then use another terminal:

```bash
ollama list
ollama run qwen3:1.7b
```

Verification: `ollama list` should show local models, and `ollama run <model>` should open a terminal chat:

![Terminal showing Ollama service status, model list, and an ollama run chat](ollama_service.png)

Do not run plain `ollama serve` unless you also set `OLLAMA_MODELS`; otherwise the daemon may use an empty default store and `ollama run <tag>` will pull instead of using this workspace's models.

Equivalent manual form:

```bash
source ./scripts/common/env.sh
export OLLAMA_MODELS
ollama serve
```

## Portable LLM Launcher

For a removable drive, use the Portable LLM Launcher:

```bash
./scripts/ollama/portable-llm-launcher.sh
```

It points `OLLAMA_MODELS` at this repo's sibling `Ollama/models/llm` directory
and prefers a bundled binary at `../bin/ollama/<os>-<arch>/ollama[.exe]`. If no
bundled binary exists, it falls back to the host's `ollama` on `PATH`.

To put the current host's Ollama binary on the removable drive:

```bash
./scripts/ollama/install-portable-llm-binary.sh
```

Use a separate port when the host already has an Ollama service:

```bash
OLLAMA_HOST=127.0.0.1:11435 ./scripts/ollama/portable-llm-launcher.sh
```

Windows users can start the same layout with:

```bat
scripts\ollama\portable-llm-launcher.cmd
```

## Service Basics

The systemd service is optional.

Configure the model store:

```bash
./scripts/setup/configure-ollama.sh --dry-run
./scripts/setup/configure-ollama.sh
```

Start and stop:

```bash
sudo systemctl start ollama
sudo systemctl status ollama
sudo systemctl stop ollama
journalctl -u ollama -f
```

Use `./scripts/ollama/start_ollama.sh` when you want the script to verify that the service's `OLLAMA_MODELS` points at the expected portable path.

## Common Commands

```bash
ollama list
ollama ps
ollama run llama3.2:3b
ollama show qwen3:4b
ollama stop qwen3:4b
```

## HTTP API

```bash
curl -s http://127.0.0.1:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Reply in one sentence: what is mmap?",
  "stream": false
}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["response"])'
```

Installed models:

```bash
curl -s http://127.0.0.1:11434/api/tags | python3 -m json.tool
```

## Shared GGUF Helpers

Install a conservative starter set of small Ollama models:

```bash
./scripts/ollama/setup-small-models.sh
```

This starter script intentionally avoids 7B+ pulls. It is friendly to CPU/SBC and small-GPU systems; larger machines can pull bigger tags from [`hardware-matching.md`](hardware-matching.md).

```bash
./scripts/ollama/pull-and-share.sh qwen3:4b
./scripts/ollama/import-to-ollama.sh my-model my-model:latest
./scripts/ollama/check-symlinks.sh
./scripts/ollama/relink-to-ollama.sh
```

These scripts use `$OLLAMA_MODELS` for Ollama CAS state and `$LLM_MODELS_DIR` for real GGUF files.

## Cline Through Ollama

The recommended Cline path is llama.cpp through `cline-server.sh` or `llama-cline.service`. The Ollama path remains useful as a fallback:

```bash
./scripts/ollama/warmup_for_cline.sh
```

In Cline:

- Provider: `Ollama`
- Base URL: `http://127.0.0.1:11434`
- Model: a tool-capable Ollama model, for example `qwen-coder-cline`

See [`cline.md`](cline.md) for the main Cline workflow.

## Troubleshooting Empty `ollama list`

If model files exist but `ollama list` is empty, check which daemon owns the port:

```bash
ss -H -tlnp '( sport = :11434 )'
pgrep -af 'ollama serve'
systemctl is-active ollama
```

If a manual daemon is listening without the right environment:

```bash
pkill -f "ollama serve"
./scripts/ollama/serve.sh
ollama list
```

For the service workflow, use:

```bash
pkill -f "ollama serve"
./scripts/ollama/start_ollama.sh
ollama list
```
