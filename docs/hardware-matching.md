# Hardware Matching

Use this guide to choose a first model set for a target machine. The root [`README.md`](../README.md) has the high-level hardware tier table; this page gives concrete machines and starter choices.

For Ollama, use:

```bash
ollama pull <tag>
```

For llama.cpp, download a GGUF from a well-maintained repo and place it in:

```text
models/<name>.gguf
```

## Example Picks

Start here if you just want a reasonable first pull for a common machine.

| Example | General chat | Coding / Cline | Context starting point | Why |
|---|---|---|---:|---|
| Single Board Computer: Raspberry Pi 5 / Orange Pi, 8 GB | `llama3.2:1b` | `qwen2.5-coder:0.5b` | 2048 | Small enough to be usable on shared RAM. |
| Used mini PC: Intel N100/N305, 16 GB | `llama3.2:1b` | `qwen2.5-coder:1.5b` | 4096 | Practical always-on local helper without GPU offload. |
| Budget Cline GPU: RTX 3060 12 GB | `qwen3:8b` | `qwen2.5-coder:7b` | 8192-16384 | 12 GB VRAM is a sweet spot for cheap local agents. |
| Strong gaming PC: RTX 4080 / 4080 Super | `mistral-nemo:12b` | `qwen2.5-coder:14b` | 16384-32768 | Enough VRAM for stronger coder models and useful context. |
| High-end single GPU: RTX 4090 / 5090 | `qwen3:30b`, `gpt-oss:20b` | `qwen2.5-coder:32b`, `qwen3-coder:30b` | 32768+ | Good target for larger agentic models. |
| High-memory Mac: Mac Studio / MacBook Pro | 7B-32B Q4 models | `qwen2.5-coder` family in Q4 | 8192-32768 | Unified memory can hold larger models, though tokens/sec varies. |

## Full Hardware Examples

These are practical starting points, not promises. Laptop GPUs, board RAM options, thermal limits, quantization, and context size can change the result a lot.

| Example hardware | Typical memory shape | Good first try | Cline / agent fit | Notes |
|---|---|---|---|---|
| Raspberry Pi 5, 4 GB | Shared system RAM | `smollm2:360m` | Poor | Use for smoke tests, tiny chat, and learning the workflow. Keep context near `2048`. |
| Raspberry Pi 5, 8 GB | Shared system RAM | `tinyllama`, `llama3.2:1b` | Poor to limited | Can run tiny models, but long Cline tasks will feel painful. |
| Orange Pi 5 / 5 Plus, 8-16 GB | Shared system RAM, RK3588-class NPU usually not useful for this stack | `llama3.2:1b`, `qwen2.5-coder:0.5b` | Limited | Better RAM headroom than small Pis; still treat it as CPU inference unless using a separate acceleration stack. |
| Used Intel N100/N305 mini PC, 16 GB | CPU RAM, no useful discrete VRAM | `qwen2.5-coder:1.5b`, `llama3.2:1b` | Limited | Nice always-on local box. Good for Ollama chat, small helpers, and demos. |
| Used office desktop, 32 GB RAM, no GPU | CPU RAM | `qwen2.5-coder:3b`, `qwen3:4b` | Limited to fair | Better for one-shot coding than full agent loops. Keep expectations sane. |
| Old gaming laptop, GTX 1650 / 1050 Ti, 4 GB VRAM | Small NVIDIA VRAM | `qwen2.5-coder-3b` with lowered context | Fair if tuned | Stop Ollama before llama.cpp. Try `N_CTX=8192` first if allocation fails. |
| RTX 3060 12 GB desktop | 12 GB VRAM | `qwen2.5-coder:7b` or a 7B coder GGUF Q4 | Good | A strong budget Cline box. 12 GB VRAM is much nicer than 8 GB for KV cache. |
| RTX 4060 Ti 16 GB desktop | 16 GB VRAM | `qwen2.5-coder:7b`, `gemma3:12b` | Good | The extra VRAM often matters more than raw GPU speed for local agents. |
| RTX 4070 / 5070 12 GB desktop | 12 GB VRAM | `qwen2.5-coder:7b`, `qwen3:8b` | Good | Fast, but 12 GB still needs context discipline. Treat 14B models as experiments. |
| RTX 5070 laptop, 8-12 GB VRAM | Laptop VRAM varies by model | `qwen2.5-coder:3b` to `7b` | Fair to good | Check the exact laptop VRAM. Power limits matter as much as the name on the sticker. |
| RTX 4080 / 4080 Super, 16 GB VRAM | 16 GB VRAM | `qwen2.5-coder:14b`, `mistral-nemo:12b` | Very good | Good daily-driver tier for Cline with Q4/Q5 models. |
| RTX 4090, 24 GB VRAM | 24 GB VRAM | `qwen2.5-coder:14b`, `starcoder2:15b`, `granite-code:20b` | Excellent | Great single-GPU local agent machine. Try larger context, then tune down if needed. |
| RTX 5090, 32 GB VRAM | 32 GB VRAM | `qwen2.5-coder:32b`, `qwen3-coder:30b`, `gpt-oss:20b` | Excellent | Strong single-GPU tier for larger agentic models and longer contexts. |
| Mac mini M4, 16-32 GB unified memory | Unified memory | `llama3.2:3b`, `qwen2.5-coder:3b` | Fair | Great quiet desktop, but unified memory is not the same as NVIDIA VRAM. Use Ollama or llama.cpp Metal builds. |
| MacBook Pro / Mac Studio, 48-128 GB unified memory | Large unified memory | 7B-32B Q4 models | Good to excellent | Very practical for quiet local LLM work. More memory helps load bigger models; GPU speed still limits tokens/sec. |
| Mac Studio Ultra-class, 192 GB+ unified memory | Very large unified memory | 32B-70B+ quantized models | Excellent for big local models | Can hold huge models, but dense giant models may still be slow. Good for private long-running work. |
| Jetson Orin Nano 8 GB | Shared LPDDR5, CUDA-capable edge device | `llama3.2:1b`, `qwen2.5-coder:0.5b` | Limited | Useful for edge demos and robotics-adjacent local inference, not heavy Cline work. |
| Jetson AGX Orin 32-64 GB | Shared LPDDR5, CUDA-capable edge device | 3B-7B quantized models | Fair to good | Better edge AI platform. Use when power envelope and embedded deployment matter. |
| Dual RTX 3090/4090/5090 workstation | Multiple 24-32 GB GPUs | 32B-70B quantized models | Excellent with extra setup | This repo's defaults are single-server/simple-service. Multi-GPU needs deliberate llama.cpp/server flags and testing. |
| GPU server / cluster, A100/H100/L40S-class | Datacenter VRAM, often 48-80 GB per GPU | 70B+ quantized or served multi-GPU models | Excellent | Usually beyond the simple local Cline service. Treat this repo as the client/workspace layer, not the whole cluster scheduler. |

The `scripts/ollama/setup-small-models.sh` helper installs a conservative sub-7B starter set. It is intentionally safe for smaller machines; high-end users should pull larger tags manually.

## Notes On Specs

- Prefer memory headroom over chasing model size. A smaller model with enough context often works better than a larger model that constantly runs out of KV cache.
- Laptop GPU names do not guarantee desktop GPU VRAM or performance. Check the exact model's VRAM and power limit.
- Apple unified memory can hold larger models than similarly priced GPUs, but NVIDIA CUDA still tends to be the smoother path for this repo's llama.cpp service workflow.
- SBCs and Jetson boards are useful for edge experiments, demos, and always-on helpers. They are usually not good first choices for Cline-heavy repo editing.
- Multi-GPU setups are powerful, but they need explicit runtime configuration. Keep the basic `llama-cline` service single-model and simple until one GPU works reliably.

## Spec References

- Raspberry Pi documentation: <https://www.raspberrypi.com/documentation/>
- Orange Pi 5 Plus product page: <https://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Orange-Pi-5-plus.html>
- NVIDIA Jetson Orin page: <https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/>
- NVIDIA RTX 3060 family page: <https://www.nvidia.com/en-us/geforce/graphics-cards/30-series/rtx-3060-3060ti/>
- NVIDIA RTX 40 Series specs: <https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/>
- NVIDIA RTX 5070 family page: <https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5070-family/>
- NVIDIA RTX 4090 page: <https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/>
- NVIDIA RTX 5090 page: <https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/>
- Apple Mac mini specs: <https://www.apple.com/mac-mini/specs/>
- Apple Mac Studio specs: <https://support.apple.com/en-us/122211>

See [`models.md`](models.md) for what the model families are designed to do.
