# Claude Code With Ollama

Claude Code is Anthropic's CLI coding agent. It speaks Anthropic's Messages
API format, which Ollama does not implement directly. A LiteLLM proxy sits
between them and translates the formats.

```
Claude Code CLI → LiteLLM proxy (port 4000) → Ollama (port 11434)
```

All three must be running when using local models.

## Critical: Thinking Param Constraint

Claude Code sends a `thinking` parameter with every request (extended
thinking). Ollama only supports this for **qwen3** models. Every other model
family (llama, phi, qwen2.5, deepseek, hermes, etc.) will return:

```
"<model>" does not support thinking
```

**Only qwen3 models work with Claude Code via this setup.**

For 4GB VRAM, `qwen3:4b` is the recommended model. It fits fully on GPU
and supports thinking natively.

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

LiteLLM is installed in a local venv:

```bash
/media/data/LLM/.local/venv/bin/litellm --version
```

Config file is at `.local/litellm_config.yaml`. It lists all installed Ollama
models. Update it whenever you add or remove models.

Install the systemd service once:

```bash
./scripts/ollama/install-litellm-service.sh
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

**LiteLLM proxy:**

```bash
sudo systemctl start litellm-proxy
```

**Claude Code:**

```bash
claude-local --model qwen3:4b
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
  ANTHROPIC_BASE_URL=http://localhost:4000 \
  ANTHROPIC_AUTH_TOKEN=ollama \
  claude "$@"
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

Only qwen3 models support Claude Code's thinking param.

| Model | VRAM | Notes |
|---|---|---|
| `qwen3:4b` | 2.5 GB | Best fit for 4–6 GB VRAM cards |
| `qwen3:8b` | ~5 GB | Better capability, needs 8 GB VRAM |
| `qwen3:1.7b` | 1.4 GB | Fits anywhere but too small for reliable tool use |

## LiteLLM Config Notes

qwen3 models require `merge_reasoning_content_in_choices: true` in
`.local/litellm_config.yaml`, otherwise Claude Code receives the thinking
block but empty response text. Example:

```yaml
  - model_name: qwen3:4b
    litellm_params:
      model: ollama/qwen3:4b
      api_base: http://localhost:11434
      merge_reasoning_content_in_choices: true
```

When adding a new qwen3 model, always include this flag.

## Switch Back To Claude Cloud

```bash
claude-cloud
```

## Verify

Check LiteLLM proxy is up:

```bash
curl -s http://localhost:4000/health
```

Quick chat test:

```bash
ANTHROPIC_BASE_URL=http://localhost:4000 \
ANTHROPIC_AUTH_TOKEN=ollama \
claude --model qwen3:4b -p "Reply with exactly: ready"
```

## Notes

- Local models handle simple edits and Q&A well. Complex multi-step agentic
  tasks are hit-or-miss — smaller models don't always follow Claude Code's
  tool-calling schema reliably.
- LiteLLM translates the API format but cannot compensate for model capability
  gaps vs actual Claude.
- For Cline-specific setup, see [`cline.md`](cline.md).
- For Copilot + Ollama setup, see [`copilot.md`](copilot.md).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Connection refused` on port 4000 | LiteLLM not running — `sudo systemctl start litellm-proxy` |
| `Connection refused` on port 11434 | Ollama not running — `./scripts/ollama/serve.sh` |
| `does not support thinking` | Wrong model — switch to a `qwen3` model |
| `cudaMalloc failed: out of memory` | Stop llama-cline — `sudo systemctl stop llama-cline` |
| Model not found | Add model to `.local/litellm_config.yaml` and restart proxy |
| Tool call failures / garbled output | Model too small. Use `qwen3:4b` or switch to `claude-cloud` |
