# Models

English | [简体中文](models.zh-CN.md)

## Tested Models

The models below are examples tested on the 6 GB reference laptop. They are
not required, exclusive, or a ceiling. Hardware with more VRAM and RAM can run
larger and more capable GGUF models.

| Model | Local file | Size | Role |
|---|---|---:|---|
| Qwen3.5-4B official Q4_K_M | `qwen3.5-4b-official-Q4_K_M.gguf` | 2.6 GB | Recommended daily agentic coding model |
| Qwen3.5-2B official Q4_K_M | `qwen3.5-2b-official-Q4_K_M.gguf` | 1.2 GB | Faster, lower-memory model with long-context options |
| Gemma 4 E4B official QAT Q4_0 | `gemma4-e4b-official-QAT-Q4_0.gguf` | 4.8 GB | General and multimodal-oriented local option |
| Qwen3.5-9B Defiant IQ3_M | `qwen3.5-9b-defiant-IQ3_M.gguf` | 5.2 GB | Experimental larger model; more CPU/RAM pressure |
| Huihui Qwen3.5-2B abliterated | Ollama tag `huihui_ai/qwen3.5-abliterated:2b-agent` | 1.9 GB | Agent-ready uncensored Ollama model; 32K context |
| Huihui Qwen3.5-2B abliterated F16 | `huihui-qwen3.5-2b-abliterated-f16.gguf` | 3.8 GB | High-precision llama.cpp GGUF; conservative 32K default |
| Huihui Qwen3.5-4B abliterated | Ollama tag `huihui_ai/qwen3.5-abliterated:4b-agent` | 3.3 GB | Agent-ready uncensored Ollama model; 32K context |

Qwen3.5-4B is the default recommendation for local coding agents on the tested
6 GB GPU. Qwen3.5-2B is useful when context size or speed matters more than
raw model capability. Use the hardware tier and model quality you need rather
than limiting the setup to these examples.

Official-compatible GGUF downloads:

```bash
curl -fL --retry 5 -C - \
  -o ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf.part \
  https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/main/Qwen3.5-4B-Q4_K_M.gguf
mv ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf.part \
  ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf

sha256sum ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf
# expected: 00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4

curl -fL --retry 5 -C - \
  -o ~/LLM/models/qwen3.5-2b-official-Q4_K_M.gguf.part \
  https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/main/Qwen3.5-2B-Q4_K_M.gguf
mv ~/LLM/models/qwen3.5-2b-official-Q4_K_M.gguf.part \
  ~/LLM/models/qwen3.5-2b-official-Q4_K_M.gguf

sha256sum ~/LLM/models/qwen3.5-2b-official-Q4_K_M.gguf
# expected: aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223
```

## Agent Fit

| Model | Claude Code | Codex CLI | Hermes |
|---|---|---|---|
| Qwen3.5-4B official | Tested | Tested | Tested |
| Qwen3.5-2B official | Supported | Supported | Tested |
| Gemma 4 E4B | Experimental | Experimental | Experimental |
| Qwen3.5-9B Defiant | Experimental | Experimental | Experimental |
| Huihui Qwen3.5-2B abliterated | Not supported by current llama.cpp build | Not tested | Ollama only; not agent-tested |
| Huihui Qwen3.5-2B abliterated F16 | llama.cpp load verified | Not tested | Not agent-tested |
| Huihui Qwen3.5-4B abliterated | Not installed for llama.cpp | Not tested | Ollama only; not agent-tested |

The tested result is protocol compatibility and successful local completion.
Small models can still make poor multi-step editing decisions or malformed
tool calls.

### Huihui Abliterated Variant

The Huihui model was installed from the publisher's Ollama tag. Its GGUF is
usable by Ollama but the installed llama.cpp build rejects its
`qwen35.rope.dimension_sections` metadata. The canonical file is therefore
stored under `~/LLM/ollama/models/external/` instead of the shared llama.cpp
model directory.

Use the agent-ready tag through Ollama:

```bash
llm start ollama huihui_ai/qwen3.5-abliterated:2b-agent
```

It is an uncensored experimental model and has not been validated for agentic
coding. Review its outputs accordingly.

The separate mradermacher F16 GGUF loads in llama.cpp and can be started with:

```bash
llm start llama-cpp huihui-qwen3.5-2b-abliterated-f16
```

Because the F16 weights consume 3.8 GB before KV cache and compute buffers, its
menu default is conservatively set to 32K context. Verified menu options are
16K, 32K, 64K, 128K, and 256K. 128K fits with the KV cache on the GPU; 256K
automatically uses `KV_OFFLOAD=0` so the cache moves to system RAM.

## Ollama Agent Tags

The imported Ollama models are rebuilt with explicit renderer/parser settings,
deterministic sampling, and larger context windows:

| Tag | Context | Tools |
|---|---:|---|
| `qwen3.5-2b-official:latest` | 64K default; up to 256K selectable | Verified |
| `qwen3.5-4b-official:latest` | 64K default; up to 128K selectable | Verified configuration |
| `huihui_ai/qwen3.5-abliterated:2b-agent` | 32K default; up to 128K selectable | Verified |
| `huihui_ai/qwen3.5-abliterated:4b-agent` | 32K default; up to 64K selectable | Verified configuration |
| `gemma4-e4b-official:latest` | 16K default; up to 64K selectable | Verified configuration |
| `qwen3.5-9b-defiant-uncensored:latest` | 16K default; up to 64K selectable | Verified configuration |

Native Ollama `/api/chat` and OpenAI-compatible
`/v1/chat/completions` both returned structured tool calls in testing.

## Context And Memory

Larger models do not automatically support more usable context. Context memory
depends on architecture, KV heads, cache type, context length, and whether the
KV cache is on the GPU.

Observed profile defaults:

| Model | Default context | GPU layers |
|---|---:|---:|
| Qwen3.5-2B | 128K | all |
| Qwen3.5-4B | 64K | all |
| Qwen3.5-9B | 32K | 24 |
| Gemma 4 E4B | 32K | 30 |

These are launch defaults, not fixed agent limits. The running server reports
the actual context to the agent.

## Model Storage

Store GGUF files in `$LLM_MODELS_DIR` and keep the repository lightweight.
Ollama should link to the same canonical files where practical.

```bash
llm models
llm models --sort name
```

Size sorting is automatic and smallest-first.

## Hermes Prompt Budget

Hermes tools and system instructions are a meaningful fraction of context for
small models. The measured default is roughly 13K input tokens before project
content. Skills are loaded progressively, but preloading large skills costs
the full skill size.

For 2B coding:

```bash
hermes-local -t terminal,file,skills,todo,clarify
```

Keep `skills` enabled for on-demand access and avoid preloading large skill
files unless the task needs them.
