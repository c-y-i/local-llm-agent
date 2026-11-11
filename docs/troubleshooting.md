# Troubleshooting

English | [简体中文](troubleshooting.zh-CN.md)

## Start Here

```bash
llm doctor
llm status
llm models
```

## `llm` Says The Managed Environment Is Not Active

`llm` still requires explicit activation:

```bash
source /home/cy/Projects/local-llm-agent/.venv/bin/activate
```

The `claude-local`, `codex-local`, and `hermes-local` commands do this
automatically and can run from any directory.

## Ollama Is `ready` But No Model Is Active

The Ollama daemon is running, but no model is loaded. This is not an active
inference backend. Start one:

```bash
llm start ollama qwen3.5-4b-official:latest
```

Or run a direct local-agent command, which starts the preferred llama.cpp model
when needed.

## Agent Starts The Wrong Model

Direct agent commands prefer the first model in the existing recommendation
order. Stop the active server before switching, or start the desired model
explicitly:

```bash
llm start llama-cpp qwen3.5-2b-official-Q4_K_M
```

Only one model can occupy llama.cpp port 8080 at a time.

## Hermes Shows A Smaller Context Window

Check the live server:

```bash
curl -s http://127.0.0.1:8080/props
```

Then check Hermes configuration:

```bash
HERMES_HOME=/home/cy/LLM/hermes-local \
  hermes config get model.context_length --json
HERMES_HOME=/home/cy/LLM/hermes-local \
  hermes config get model.ollama_num_ctx --json
```

Remove a conflicting pin and restart Hermes:

```bash
HERMES_HOME=/home/cy/LLM/hermes-local \
  hermes config unset model.context_length
HERMES_HOME=/home/cy/LLM/hermes-local \
  hermes config unset model.ollama_num_ctx
```

For Ollama, also verify both runtime and tag settings:

```bash
ollama ps
ollama show MODEL --modelfile | grep 'PARAMETER num_ctx'
```

These values must match. Starting through `llm start ollama --context ...`
reloads the model, updates the tag, and invalidates Hermes's stale cache.

## CUDA Out Of Memory

The CLI normally enforces one engine at a time. If a legacy server is still
running, stop it before starting another:

```bash
llm status
ollama ps
nvidia-smi
```

Then reduce context, reduce GPU layers, or offload the KV cache:

```bash
llm start llama-cpp MODEL --context 32768
llm start llama-cpp MODEL --gpu-layers 24
KV_OFFLOAD=0 llm start llama-cpp MODEL --context 65536
```

## Background llama.cpp Fails

Inspect the managed log and PID:

```bash
tail -n 100 ~/LLM/run/llama-server.log
cat ~/LLM/run/llama-server.pid
```

Check whether another process owns port 8080:

```bash
ss -ltnp '( sport = :8080 )'
```

## Ollama Logs Are Not Visible

Ollama runs inside a daemon, not as a foreground child of the agent command.
Use the managed log:

```bash
llm logs --backend ollama
llm logs --backend ollama --follow
```

If `$LLM_ROOT/run/ollama.log` does not exist, start Ollama through
`llm start ollama`; this launches a managed daemon with persistent logging.

## Agent Tool Calls Are Unreliable

- Use Qwen3.5-4B before Qwen3.5-2B for complex multi-step editing.
- Reduce the Hermes toolset for small models.
- Do not preload large skills unless needed.
- Keep repository instructions short.
- Use Git or a disposable branch.

For lean Hermes coding:

```bash
hermes-local -t terminal,file,skills,todo,clarify
```

## Runtime Inspection

```bash
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8080/props
curl -s http://127.0.0.1:8080/slots
curl -s http://127.0.0.1:8080/metrics
curl -s http://127.0.0.1:11434/api/ps
```
