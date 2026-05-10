# Models

English | [简体中文](models.zh-CN.md)

This is an example catalog of model families and what they are generally useful for in a local-agent workspace. It intentionally does not try to match models to hardware; use [`hardware-matching.md`](hardware-matching.md) for that.

Your installed models are whatever appears in:

```bash
./scripts/llama-cpp/llm-list.sh
ollama list
```

Keep large GGUF files in `models/`; they are ignored by Git.

## Discovery Sources

- Ollama library: <https://ollama.com/library>
- Hugging Face models with `llama.cpp` support: <https://huggingface.co/models?other=llama.cpp>

Prefer official or well-maintained model pages, recent quantizations, clear licenses, and model families that fit the task.

## Model Roles

| Role | What to look for | Good for | Watch out for |
|---|---|---|---|
| General chat | Instruct/chat model, broad language coverage | Q&A, drafting, summaries, everyday assistant use | May be weaker at exact tool-call formats. |
| Coding | Code-tuned or coder model | Editing code, explaining errors, repo navigation, Cline | General prose can feel less natural. |
| Tool / agent | Tool/function tags, strong instruction following | Cline, automation loops, structured responses | Some models still emit malformed tool calls. |
| Reasoning | Thinking/reasoning tags | Math, planning, solo analysis | Thinking text can confuse agent tool protocols. |
| Vision | Vision/multimodal tags | Images, screenshots, OCR-like workflows | Usually heavier and not needed for text-only Cline. |
| Embedding | Embedding tag/model | Search, retrieval, clustering | Not a chat model. |

## Example Catalog

| Model / family | Role | What it does |
|---|---|---|
| `qwen2.5-coder` | Coding / agent | Code-focused Qwen family with small through large sizes; good Cline candidate. |
| `qwen3-coder` | Coding / agent | Agentic coding family for larger local setups. |
| `starcoder2` | Coding | Code model family with 3B/7B/15B-style sizing. |
| `codegemma` | Coding | Lightweight coding-oriented Gemma variants. |
| `granite-code` | Coding | IBM code model family, useful for code intelligence experiments. |
| `llama3.2` | General chat | Small Llama family, useful for general chat and simple local tasks. |
| `qwen3` | General / reasoning | Broad dense and MoE Qwen family; some tags may emit thinking text. |
| `gemma3` / `gemma4` | General / multimodal / agent | Modern Gemma families with text, tool, and multimodal-oriented tags. `gemma4:e4b` is a tested Ollama pick for Cline/Ollama agent work on an RTX 3050 laptop with 6 GB VRAM. |
| `mistral` / `mistral-nemo` / `mistral-small` | General / tool | Mistral family for chat, tools, and larger-context experiments. |
| `phi4-mini` | General / tool | Compact instruction-following model; useful as a terse fallback. |
| `deepseek-r1` | Reasoning | Strong reasoning family; usually better for solo reasoning than Cline tool loops. |
| `gpt-oss` | Reasoning / agent | Open-weight reasoning and agentic family in larger sizes. |
| `tinyllama` | Tiny general chat | Very small baseline for constrained devices and smoke tests. |
| `smollm2` | Tiny general chat | Compact model family with very small and 1.7B-class sizes. |
| `nomic-embed-text`, `bge-m3`, `embeddinggemma` | Embedding | Retrieval/search embeddings; not used as Cline chat models. |
| GGUF repos tagged `llama.cpp` | Runtime format | Quantized model files for llama.cpp; choose family and quantization by use case. |

## Local Names

This repo may use local file names that differ from Ollama tags:

| Local name | Meaning |
|---|---|
| `qwen2.5-coder-3b` | GGUF file expected at `models/qwen2.5-coder-3b.gguf`. |
| `llama3.2-3b` | GGUF file expected at `models/llama3.2-3b.gguf`. |
| `qwen3-1.7b` | GGUF file expected at `models/qwen3-1.7b.gguf`. |
| `qwen-coder-cline` | Legacy Ollama personality overlay for Cline-style use. |

## Cline Defaults

`cline-server.sh` uses model-specific context defaults for known local GGUF names:

| Model | Context |
|---|---:|
| `qwen2.5-coder-3b` | 32768 |
| `llama3.2-3b` | 12288 |
| `qwen3-1.7b` | 12288 |
| `qwen3-4b` | 8192 |
| `phi4-mini` | 8192 |

Set Cline's Context Window Size to the value printed by the wrapper or `llama-cline.service`.

## Claude Code Compatibility

Claude Code sends Anthropic Messages requests that Ollama does not implement
directly. Use `scripts/ollama/anthropic-proxy.py` through `claude-local`; the
launcher opens a picker when no model is specified and puts currently loaded
Ollama models first.

| Model | Works with Claude Code | Notes |
|---|---|---|
| `qwen2.5-coder` | Yes, via proxy | Best current local Claude Code default; `qwen2.5-coder:3b` is verified |
| `llama3.2` | Partial, via proxy | General fallback; weaker at tool use |
| `phi4-mini` | Partial, via proxy | Compact fallback |
| `qwen3` | Unreliable | Can spend output budget on reasoning and return empty content |
| `deepseek-r1` | Poor | Reasoning tags often confuse agent protocols |
| `hermes3` | Experimental | May emit malformed tool calls |

For 4GB VRAM cards, `qwen2.5-coder:3b` is the recommended Claude Code model.
Run `claude-local` to pick from installed models. See
[`claude-code.md`](claude-code.md) for full setup.

## Tool Use

Cline and other agent loops need models/templates that can follow tool-call instructions reliably. If a model repeatedly emits malformed XML tool calls, use the guardrails in `.clinerules` and [`cline.md`](cline.md), or switch to a more code/tool-tuned model.

## Updating This File

After changing your local model set, update this catalog to describe what each model is for. Put hardware-specific advice in [`hardware-matching.md`](hardware-matching.md), and do not commit model weights.
