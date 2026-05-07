# Using llama.cpp

These commands use the portable defaults from `scripts/common/env.sh`.

## List Models

```bash
./scripts/llama-cpp/llm-list.sh
```

## Interactive Or One-Shot

```bash
./scripts/llama-cpp/llm-run.sh qwen3-4b
./scripts/llama-cpp/llm-run.sh qwen3-4b "Explain TCP slow start in two sentences."
```

## Direct llama.cpp Invocation

```bash
$LLAMA_CPP_BIN \
  -m "$LLM_MODELS_DIR/qwen3-4b.gguf" \
  -ngl 999 -c 4096 \
  -p "Hello"
```

If the environment variables are not set in your shell, run:

```bash
source ./scripts/common/env.sh
```

## OpenAI-Compatible Server

```bash
./scripts/llama-cpp/llm-serve.sh qwen2.5-coder-3b 8080
```

Endpoints:

- `POST http://127.0.0.1:8080/v1/chat/completions`
- `POST http://127.0.0.1:8080/v1/completions`
- `GET  http://127.0.0.1:8080/v1/models`

Quick test:

```bash
curl http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"hi"}],"max_tokens":32}'
```

## Cline Server

Foreground:

```bash
./scripts/llama-cpp/cline-server.sh
```

Manual systemd service:

```bash
./scripts/setup/install-llama-cline-service.sh
sudo systemctl start llama-cline
sudo systemctl status llama-cline
```

Configure Cline with Base URL `http://127.0.0.1:8080/v1`, the model printed by the wrapper, and the printed `Context` value. Full guide: [`cline.md`](cline.md).

## Environment Knobs

| Variable | Default |
|---|---|
| `N_GPU_LAYERS` | `999` |
| `N_CTX` | wrapper-specific default |
| `HOST` | `127.0.0.1` |
| `LLAMA_CPP_ROOT` | `../llama-cpp` |
| `LLAMA_CPP_BIN` | `$LLAMA_CPP_ROOT/build/bin/llama-cli` |
| `LLAMA_SERVER_BIN` | `$LLAMA_CPP_ROOT/build/bin/llama-server` |
| `LLM_MODELS_DIR` | `./models` |

Example:

```bash
N_GPU_LAYERS=16 ./scripts/llama-cpp/llm-run.sh qwen3-4b "hi"
```

## VRAM Coordination With Ollama

On small GPUs, do not keep an Ollama runner loaded while starting llama.cpp with full GPU offload.

```bash
ollama ps
sudo systemctl stop ollama
sudo systemctl start llama-cline
```

`llama-cline.service` stops `ollama.service` before loading the model.
