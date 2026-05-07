# Maintenance

## Add Models

Pull from Ollama and share the GGUF with llama.cpp:

```bash
./scripts/ollama/pull-and-share.sh qwen3:4b
```

Import a GGUF already placed in `models/`:

```bash
./scripts/ollama/import-to-ollama.sh my-model my-model:latest
```

List and audit:

```bash
./scripts/llama-cpp/llm-list.sh
ollama list
./scripts/ollama/check-symlinks.sh
```

## Remove Models

Remove from both Ollama and the shared model directory:

```bash
./scripts/ollama/remove-model.sh qwen3:4b
```

Avoid deleting only one side unless you intentionally want to repair the symlink layer later.

## Relink Ollama CAS

If Ollama rewrites a real blob where a symlink used to be:

```bash
./scripts/ollama/relink-to-ollama.sh qwen3:4b
./scripts/ollama/check-symlinks.sh
```

## Update llama.cpp

```bash
./scripts/setup/build-llama-cpp.sh --dry-run
./scripts/setup/build-llama-cpp.sh
```

## Manage Services

Ollama:

```bash
./scripts/setup/configure-ollama.sh
sudo systemctl start ollama
sudo systemctl stop ollama
```

Cline llama.cpp service:

```bash
./scripts/setup/install-llama-cline-service.sh
sudo systemctl start llama-cline
sudo systemctl stop llama-cline
journalctl -u llama-cline -f
```

Keep `llama-cline` disabled for autostart:

```bash
sudo systemctl disable llama-cline
```

## Troubleshooting

### `ollama list` is empty

Check whether a manual Ollama daemon is using a different model store:

```bash
ss -H -tlnp '( sport = :11434 )'
pgrep -af 'ollama serve'
```

Then restart the manual server with the repo's model store:

```bash
pkill -f "ollama serve"
./scripts/ollama/serve.sh
```

### `llama-cline` cannot allocate CUDA memory

Stop Ollama or lower offload/context:

```bash
nvidia-smi
ollama ps
sudo systemctl stop ollama
sudo systemctl restart llama-cline
```

### Permission denied on GGUF files

Make files readable by the user running llama.cpp and by the Ollama service user:

```bash
chmod 644 models/*.gguf
```

If your Ollama service runs under an `ollama` group, group-readable files are enough.

## Backup

Back up this repo's scripts/docs/config and your `models/` directory intentionally. Avoid backing up both `models/` and Ollama CAS symlinks with dereference enabled, or you may duplicate large files.
