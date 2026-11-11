# Context And Memory

English | [简体中文](context-memory.zh-CN.md)

## One Source Of Truth

The running backend owns the context window. Agent launchers read the live
server value. Avoid static client-side context pins that can silently override
the model server.

For llama.cpp:

```bash
curl -s http://127.0.0.1:8080/props
curl -s http://127.0.0.1:8080/v1/models
```

Both expose the allocated `n_ctx`. The model's training limit may be larger or
equal to the allocated window.

## Context, KV Cache, And Files

| Item | Persists? | Purpose |
|---|---|---|
| Context window | No | Maximum tokens considered in one request |
| KV cache | No | Runtime attention state, usually in VRAM or RAM |
| Chat/session state | Agent-dependent | Conversation history |
| Repository files | Yes | Project code, instructions, and documentation |
| Agent instructions | Yes | `AGENTS.md`, Hermes `SOUL.md`, and similar files |

Files are not automatically remembered. The agent must search or read them
during a task.

## Choosing A Context Size

Higher values allow longer conversations and larger repository slices but cost
more memory and reduce cache headroom:

- 16K-32K: conservative, fast, good for small edits.
- 64K: practical default for Qwen3.5-4B coding work.
- 128K: useful for broader repository work or long sessions.
- 256K: experimental on this hardware; expect slower prefill and high memory
  pressure.

Qwen3.5-2B has a native 262,144-token limit. It was verified at 128K with the
KV cache on the GPU and at 256K with `KV_OFFLOAD=0`.

## llama.cpp Controls

```bash
llm start llama-cpp qwen3.5-4b-official-Q4_K_M --context 65536
llm start llama-cpp qwen3.5-4b-official-Q4_K_M --gpu-layers 24
```

Environment overrides:

```bash
KV_CACHE_TYPE=q8_0 \
  llm start llama-cpp qwen3.5-4b-official-Q4_K_M --context 65536

KV_CACHE_TYPE=q4_0 KV_OFFLOAD=0 \
  llm start llama-cpp qwen3.5-2b-official-Q4_K_M --context 262144
```

Lower GPU layers move model layers to CPU/RAM. Disabling KV offload moves the
cache itself to CPU/RAM.

## Hermes Context

Hermes must not keep a global `model.context_length` or
`model.ollama_num_ctx` when the intent is to follow the active backend. The
launcher detects conflicts and reports the exact setting to remove.

Agent-specific instruction files still consume context. Keep them short and
load detailed procedures on demand.

## Debugging

```bash
llm status
curl -s http://127.0.0.1:8080/props
curl -s http://127.0.0.1:8080/slots
curl -s http://127.0.0.1:8080/metrics
ollama ps
nvidia-smi
```
