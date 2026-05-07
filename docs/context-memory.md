# Context And Memory

Local agent setups use several different things that people casually call "memory." They behave differently.

## Types Of Memory

| Kind | What it is | Persists? | Main limit |
|---|---|---:|---|
| Model context | Tokens sent in the current request: prompt, tools, files, conversation | No | Context window and KV cache |
| KV cache | Runtime cache for the current context tokens | No | VRAM/RAM |
| Project rules | Files like `.clinerules` that the agent reads into prompts | Yes | Only helps if included in context |
| Repo/docs | Markdown, code, configs, scripts | Yes | Agent must search/read them |
| Ollama model store | Manifests, blobs, Modelfiles | Yes | Disk |
| llama.cpp prompt cache | Optional server-side prompt reuse | Runtime-dependent | Cache settings and server lifecycle |

## Context Window

The context window is the maximum number of tokens the model can consider in one request. Agent tools can spend a lot of that budget before your actual message because they include tool schemas, rules, file summaries, and conversation history.

For Cline, set the Context Window Size to the value printed by:

```bash
./scripts/llama-cpp/cline-server.sh
```

or by:

```bash
sudo systemctl status llama-cline
```

Do not assume every model can use the same context size. A smaller model can still have a larger KV cache per token than a larger-looking model. A Raspberry Pi-class CPU setup may need 2k-4k context, while a high-end GPU can often use much larger contexts with the right quantization and KV settings.

## KV Cache And VRAM

KV cache is the runtime memory used to hold attention keys/values for the current context. It grows with:

- context size,
- number of layers,
- number of KV heads,
- KV precision,
- number of parallel slots.

Symptoms of too much KV pressure:

- `cudaMalloc failed: out of memory`,
- `unable to allocate CUDA0 buffer`,
- server starts with one model but crashes with a larger context,
- Ollama and llama.cpp cannot run at the same time.

Fixes:

```bash
sudo systemctl stop ollama
N_CTX=8192 ./scripts/llama-cpp/cline-server.sh <model>
N_GPU_LAYERS=16 ./scripts/llama-cpp/cline-server.sh <model>
```

For CPU-only or SBC systems, use very small models, low context, and `N_GPU_LAYERS=0` if your llama.cpp build expects that style of CPU-only execution.

## Persistent Project Memory

Use repo files for durable memory:

- `.clinerules` for agent behavior and tool-use guardrails,
- `README.md` for the public quick-start,
- `docs/*.md` for workflows and troubleshooting,
- source-controlled scripts for repeatable operations.

These are not automatically "known" forever. The agent must include them in context or search/read them during the task.

## Practical Defaults

For agentic coding:

- prefer a code/tool-tuned model over a general chat model,
- keep `Temperature` around `0.2`,
- set Cline's Context Window Size to the wrapper's printed context,
- use `.clinerules` for tool-call formatting guardrails,
- keep Ollama stopped when `llama-cline` needs full GPU memory.

Hardware-specific defaults:

| Hardware | Starting point |
|---|---|
| Raspberry Pi / SBC | 0.5B-1.5B model, Q4 or smaller, 2k-4k context, short tasks. |
| CPU laptop | 1B-7B Q4, 4k-8k context, expect slower agent loops. |
| Small GPU | 1B-4B Q4, model-specific context, avoid competing services. |
| Mid/high GPU | 7B-32B+ quantized, larger context, better Cline reliability. |

See [`hardware-matching.md`](hardware-matching.md) for specific starter model recommendations by hardware tier.

## Debug Commands

```bash
./scripts/common/gpu-status.sh
./scripts/llama-cpp/cline-status.sh
nvidia-smi
ollama ps
```
