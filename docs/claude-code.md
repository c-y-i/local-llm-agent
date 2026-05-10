# Claude Code With Ollama

English | [简体中文](claude-code.zh-CN.md)

Claude Code is Anthropic's CLI coding agent. It speaks Anthropic's Messages
API format, which Ollama does not implement directly. This repo uses a small
local Anthropic-compatible proxy between Claude Code and Ollama.

```
Claude Code CLI -> anthropic-proxy (port 4000) -> Ollama (port 11434)
```

All three must be running when using local models.

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
/media/data/LLM/scripts/ollama/anthropic-proxy.py
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
claude-local --model qwen2.5-coder:3b
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
function claude-local() {
  /media/data/LLM/scripts/ollama/claude-local.sh "$@"
}

function claude-cloud() {
  unset ANTHROPIC_BASE_URL
  unset ANTHROPIC_AUTH_TOKEN
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

Running `claude-local` with no arguments opens a local model picker. Models
currently loaded by Ollama are shown first and marked `RUNNING`; pressing Enter
selects the first model. If no model is loaded, preferred Claude Code models
such as `qwen2.5-coder:3b` are listed before the rest. If you pass `--model`,
the picker is skipped:

```bash
claude-local                         # pick from installed Ollama models
claude-local --model qwen2.5-coder:3b # skip picker
claude-local -p "hi"                 # pick first, then run the prompt
```

In an interactive terminal, use Up/Down arrows or `j`/`k` to move, Enter to
select, `q` to quit, or type a model number directly.

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

Check the Claude Code proxy is up:

```bash
curl -s http://localhost:4000/health
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
