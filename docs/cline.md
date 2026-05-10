# Cline Integration

English | [简体中文](cline.zh-CN.md)

Recommended path for GGUF files: Cline -> OpenAI-compatible provider -> local llama.cpp server.

Ollama also works, especially when you want to use installed Ollama tags directly.

## Start The Server

Foreground:

```bash
./scripts/common/gpu-status.sh
./scripts/llama-cpp/cline-server.sh
```

Manual systemd service:

```bash
./scripts/setup/install-llama-cline-service.sh
sudo systemctl start llama-cline
sudo systemctl status llama-cline
journalctl -u llama-cline -f
```

Stop it:

```bash
sudo systemctl stop llama-cline
```

The service does not autostart. It stops `ollama.service` first to free GPU memory.

## Cline Settings: llama.cpp

| Cline field | Value |
|---|---|
| API Provider | `OpenAI Compatible` |
| Base URL | `http://127.0.0.1:8080/v1` |
| API Key | `114514` |
| Model ID | model printed by `cline-server.sh` |
| Context Window Size | printed `Context` value |
| Temperature | `0.2` |
| Max Tokens | `1024` to `2048` |

Default model: `qwen2.5-coder-3b`.

## Cline Settings: Ollama

Start Ollama and warm a model:

```bash
sudo systemctl stop llama-cline
./scripts/ollama/serve.sh
./scripts/ollama/warmup_for_cline.sh
```

Then configure Cline:

| Cline field | Value |
|---|---|
| API Provider | `Ollama` |
| Base URL | `http://127.0.0.1:11434` |
| API Key | `114514` if Cline asks for one |
| Model ID | an installed Ollama tag, e.g. `qwen-coder-cline` |
| Context Window Size | model-specific, start with `4096` to `8192` |
| Temperature | `0.2` |
| Max Tokens | `1024` to `2048` |

If your Cline build uses OpenAI-compatible settings for Ollama, use `http://127.0.0.1:11434/v1` as the Base URL and `114514` as the API key.

When Cline is connected to Ollama, the chat panel should show the local model and run tasks normally:

![Cline running with a local Ollama model](../media/cline_demo.png)

## Model Context Defaults

The wrapper chooses conservative defaults because KV-cache size varies by model and GPU.

| Model | Context |
|---|---:|
| `qwen2.5-coder-3b` | 32768 |
| `llama3.2-3b` | 12288 |
| `qwen3-1.7b` | 12288 |
| `qwen3-4b` | 8192 |
| `phi4-mini` | 8192 |

Override only when you know it fits:

```bash
N_CTX=8192 ./scripts/llama-cpp/cline-server.sh llama3.2-3b
```

## Custom Instructions

Small local models may choose the wrong Cline XML tool or omit required fields. Use project `.clinerules` plus these Cline Custom Instructions:

```text
This Cline session is in Act mode.
Do not use plan_mode_respond unless I explicitly ask for a plan only.
Do not stop after writing a plan. Use tools to inspect, edit, test, and verify.
If I name a file, search the workspace before asking where it is.
Do not use ask_followup_question for information that can be discovered with tools.

If ask_followup_question is truly required, include:
<ask_followup_question>
<question>Ask one concise, specific question here.</question>
</ask_followup_question>

When the task is complete, include:
<attempt_completion>
<result>Briefly describe what changed and how it was verified.</result>
</attempt_completion>
```

## Verify

```bash
curl -fsS http://127.0.0.1:8080/v1/models | python3 -m json.tool | head
curl -sS http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Reply with exactly: ready"}],"max_tokens":12}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["choices"][0]["message"]["content"])'
```

Expected output: `ready`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Connection refused | Start `cline-server.sh` or `sudo systemctl start llama-cline`; check the port. |
| CUDA allocation failure | Stop Ollama, lower `N_CTX`, or lower `N_GPU_LAYERS`. |
| Cline waits after "Plan Created" | Stop the task and restart with Act-mode instructions; the model likely emitted `plan_mode_respond`. |
| `attempt_completion` missing `result` | Add the Custom Instructions above and restart the task. |
| `ask_followup_question` missing `question` | Tell Cline to search the workspace first and only ask if blocked. |
| Gibberish or loops | Ensure Cline Context Window Size matches the wrapper's printed `Context`. |

## Ollama Fallback

Stop llama.cpp and warm an Ollama model:

```bash
sudo systemctl stop llama-cline
./scripts/ollama/serve.sh
./scripts/ollama/warmup_for_cline.sh
```

Then configure Cline's Ollama provider with `http://127.0.0.1:11434`, or OpenAI-compatible mode with `http://127.0.0.1:11434/v1` and API key `114514`.
