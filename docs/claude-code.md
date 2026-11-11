# Claude Code With Local Backends

English | [简体中文](claude-code.zh-CN.md)

Claude Code sends requests to Anthropic's Messages API. Recent llama.cpp, vLLM,
and Strata releases implement that API directly, so no proxy is needed for
those backends.

| Backend | Claude Code base URL | Compatibility |
|---|---|---|
| llama.cpp | `http://127.0.0.1:8080` | Native `/v1/messages` |
| vLLM | `http://127.0.0.1:8000` | Native `/v1/messages` |
| Strata | `http://127.0.0.1:8082` | Native `/v1/messages` |
| Ollama | `http://127.0.0.1:4000` | Compatibility proxy to Ollama `:11434` |

Use the backend-neutral launcher:

```bash
./scripts/claude/claude-local.sh --backend llama-cpp --model <model>
./scripts/claude/claude-local.sh --backend vllm --model <served-model-id>
./scripts/claude/claude-local.sh --backend strata --model <model-id>
./scripts/claude/claude-local.sh --backend ollama --model <ollama-tag>
```

Install the official Claude Code CLI first if `claude` is not on `PATH`:
<https://code.claude.com/docs/en/setup>

If `--backend` is omitted, the launcher checks llama.cpp, vLLM, Strata, and the
Ollama proxy in that order. `--check` validates a backend without launching
Claude Code.

The launcher sets `CLAUDE_CODE_MAX_CONTEXT_TOKENS=32768` by default so Claude
Code does not assume an unrecognized local model has a 200K context window.
Override it to match the server:

```bash
CLAUDE_CODE_MAX_CONTEXT_TOKENS=65536 \
  ./scripts/claude/claude-local.sh --backend llama-cpp --model <model>
```

Claude Code may print an `[claude-code:unrecognized_model]` diagnostic for a
local model ID. It is harmless when the backend responds successfully; the
launcher registers the selected model and disables nonessential traffic.

## llama.cpp

Start a tool-capable GGUF with:

```bash
./scripts/llama-cpp/claude-server.sh <model>
```

This wrapper enables llama.cpp's Jinja chat templates, exposes a stable model
alias, limits parallel slots to one, and serves both:

```text
OpenAI:    http://127.0.0.1:8080/v1
Anthropic: http://127.0.0.1:8080/v1/messages
```

Then launch Claude Code:

```bash
./scripts/claude/claude-local.sh --backend llama-cpp --model <model>
```

The equivalent direct environment is:

```bash
ANTHROPIC_BASE_URL=http://127.0.0.1:8080 \
ANTHROPIC_AUTH_TOKEN=local \
ANTHROPIC_MODEL=<model> \
claude --model <model>
```

Use a current llama.cpp build. Native Anthropic Messages support was added in
2026; older binaries only expose the OpenAI API.

## vLLM And Strata

Start vLLM:

```bash
./scripts/vllm/serve.sh Qwen/Qwen3.5-4B
```

Start Strata:

```bash
STRATA_FAMILY=qwen STRATA_MODEL=q2_0 ./scripts/strata/serve.sh
```

Full backend setup:

- [`usage-vllm.md`](usage-vllm.md)
- [`usage-strata.md`](usage-strata.md)

## Ollama Proxy

Ollama does not implement Anthropic's Messages API directly, so this repo keeps
a compatibility proxy for Ollama:

```text
Claude Code CLI -> anthropic-proxy :4000 -> Ollama :11434
```

Start Ollama and the proxy, then use the launcher:

```bash
./scripts/ollama/serve.sh
sudo systemctl start litellm-proxy
./scripts/claude/claude-local.sh --backend ollama --model qwen2.5-coder:3b
```

## Critical: Thinking Param Handling

Claude Code sends a `thinking` parameter with every request (extended
thinking). Ollama's OpenAI-compatible endpoint and LiteLLM can mishandle that
for local models:

```
"<model>" does not support thinking
```

or a LiteLLM validation error for `thinking_blocks.*.signature`.

Use `scripts/ollama/anthropic-proxy.py` on port 4000. It drops Claude Code's
Anthropic-only thinking parameter before forwarding requests to Ollama. For
Qwen3 models, it also injects `/no_think` and strips leaked `<think>` text from
responses. Qwen3 can still spend the whole response budget on hidden
reasoning, so prefer `qwen2.5-coder:3b` for Claude Code on this machine.

## Critical: GPU Memory Conflict

The llama-cline service holds ~3.3GB VRAM. Stop it before using Claude Code
with Ollama or the model will fail to load:

```bash
sudo systemctl stop llama-cline
```

To go back to Cline after using Claude Code locally:

```bash
sudo systemctl stop litellm-proxy
sudo systemctl start llama-cline
```

## Prerequisites

The proxy script is:

```bash
scripts/ollama/anthropic-proxy.py
```

Proxy internals, including the optional filesystem intent router, are documented
in [`claude-proxy.md`](claude-proxy.md).

`.local/litellm_config.yaml` is kept for older LiteLLM experiments, but it is
not the recommended Claude Code path.

Install the systemd service once:

```bash
./scripts/ollama/install-claude-proxy-service.sh
```

## Start Services

**Stop llama-cline first to free VRAM:**

```bash
sudo systemctl stop llama-cline
```

**Ollama:**

```bash
./scripts/ollama/serve.sh
```

**Claude Code proxy:**

```bash
sudo systemctl start litellm-proxy
```

**Claude Code:**

```bash
./scripts/claude/claude-local.sh --backend ollama --model qwen2.5-coder:3b
```

**Service controls:**

```bash
sudo systemctl status litellm-proxy
sudo systemctl stop litellm-proxy
journalctl -u litellm-proxy -f
```

## Shell Shortcuts

Add to `~/.bashrc`:

```bash
export LOCAL_LLM_AGENT_ROOT="$HOME/Projects/local-llm-agent"

function claude-local() {
  "$LOCAL_LLM_AGENT_ROOT/scripts/claude/claude-local.sh" "$@"
}

function claude-cloud() {
  unset ANTHROPIC_MODEL
  unset ANTHROPIC_BASE_URL
  unset ANTHROPIC_AUTH_TOKEN
  unset ANTHROPIC_API_KEY
  claude "$@"
}
```

Reload:

```bash
source ~/.bashrc
```

## Recommended Models

The proxy path can run non-Qwen3 models because it removes Claude Code's
Anthropic thinking parameter before forwarding to Ollama.

The backend-neutral launcher uses the backend model list. If the server
reports exactly one model, it selects that model automatically. Otherwise,
pass `--model`. For Ollama, choose an installed tag:

```bash
ollama list
claude-local --backend ollama --model qwen2.5-coder:3b
claude-local --check                 # validate without launching Claude
```

| Model | VRAM | Notes |
|---|---|---|
| `qwen2.5-coder:3b` | 1.9 GB | Fast small coding model; verified through Claude Code |
| `qwen2.5-coder:7b` | 4.7 GB | Stronger coding model, but may exceed 4 GB VRAM |
| `qwen3:4b` | 2.5 GB | Starts, but unreliable: can return empty content after reasoning |
| `llama3.2:3b` | 2.0 GB | General fallback; weaker at tool use |
| `qwen3:1.7b` | 1.4 GB | Fits anywhere but too small for reliable tool use |

## Switch Back To Claude Cloud

```bash
claude-cloud
```

## Verify

Check the selected backend and model:

```bash
./scripts/claude/claude-local.sh --backend llama-cpp --check
./scripts/claude/claude-local.sh --backend vllm --check
./scripts/claude/claude-local.sh --backend strata --check
curl -s http://localhost:4000/health  # Ollama proxy
```

Quick chat test:

```bash
ANTHROPIC_BASE_URL=http://localhost:4000 \
ANTHROPIC_AUTH_TOKEN=ollama \
claude --model qwen2.5-coder:3b -p "Reply with exactly: ready"
```

## Notes

- Local models handle simple edits and Q&A well. Complex multi-step agentic
  tasks are hit-or-miss — smaller models don't always follow Claude Code's
  tool-calling schema reliably.
- The proxy suppresses common fake tool-call JSON for greetings and placeholder
  paths. If a local model keeps inventing tools, switch to a stronger model or
  `claude-cloud`.
- The proxy translates the API format but cannot compensate for model
  capability gaps vs actual Claude.
- For Cline-specific setup, see [`cline.md`](cline.md).
- For Copilot + Ollama setup, see [`copilot.md`](copilot.md).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Connection refused` on port 4000 | Claude Code proxy not running - `sudo systemctl start litellm-proxy` |
| `Connection refused` on port 11434 | Ollama not running - `./scripts/ollama/serve.sh` |
| `does not support thinking` | You are bypassing `anthropic-proxy.py`; make `ANTHROPIC_BASE_URL=http://localhost:4000` |
| `thinking_blocks.*.signature` | You are using LiteLLM's Anthropic path; use the repo proxy service instead |
| Empty response from `qwen3:*` | Use `qwen2.5-coder:3b`; Qwen3 can spend the response budget on reasoning |
| `cudaMalloc failed: out of memory` | Stop llama-cline — `sudo systemctl stop llama-cline` |
| Model not found | Pull it with `ollama pull <model>` and retry |
| Tool call failures / garbled output | Model too small. Try `qwen2.5-coder:7b` or switch to `claude-cloud` |
