# Claude Code With Ollama

Claude Code is Anthropic's CLI coding agent. It speaks Anthropic's Messages
API format, which Ollama does not implement directly. A LiteLLM proxy sits
between them and translates the formats.

```
Claude Code CLI → LiteLLM proxy (port 4000) → Ollama (port 11434)
```

All three must be running when using local models.

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

**Ollama:**

```bash
./scripts/ollama/serve.sh
```

**LiteLLM proxy (systemd):**

```bash
sudo systemctl start litellm-proxy
# or use the shell shortcut:
litellm-start
```

**Claude Code:**

```bash
claude-local --model qwen2.5-coder:7b
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
LITELLM_BIN="/media/data/LLM/.local/venv/bin/litellm"
LITELLM_CONFIG="/media/data/LLM/.local/litellm_config.yaml"

function litellm-start() {
  $LITELLM_BIN --config $LITELLM_CONFIG --port 4000 &
  echo "LiteLLM proxy started on port 4000 (PID $!)"
}

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

## Switch Back To Claude Cloud

```bash
claude-cloud
```

Or manually:

```bash
unset ANTHROPIC_BASE_URL
unset ANTHROPIC_AUTH_TOKEN
claude
```

## Recommended Models

| Model | Use case |
|---|---|
| `qwen2.5-coder:7b` | Best local option for agentic coding tasks |
| `deepseek-r1:7b` | Reasoning-heavy tasks |
| `qwen3:4b` | Lighter alternative when GPU memory is tight |

## Verify

Check LiteLLM proxy is up and can see the model:

```bash
curl -s http://localhost:4000/v1/models | python3 -m json.tool | grep model_name
```

Quick chat test:

```bash
ANTHROPIC_BASE_URL=http://localhost:4000 \
ANTHROPIC_AUTH_TOKEN=ollama \
claude --model qwen2.5-coder:7b -p "Reply with exactly: ready"
```

Expected output: `ready`.

## Notes

- Local models handle simple edits and Q&A well. Complex multi-step agentic
  tasks (tool chains, file editing loops) are hit-or-miss — smaller models
  don't always follow Claude Code's tool-calling schema reliably.
- LiteLLM translates the API format but cannot compensate for model capability
  gaps vs actual Claude.
- For Cline-specific setup, see [`cline.md`](cline.md).
- For Copilot + Ollama setup, see [`copilot.md`](copilot.md).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Connection refused` on port 4000 | LiteLLM proxy is not running — run `litellm-start`. |
| `Connection refused` on port 11434 | Ollama is not running — run `./scripts/ollama/serve.sh`. |
| Model not found error | Check model name matches an entry in `.local/litellm_config.yaml`. |
| Tool call failures / garbled output | Expected with smaller models. Try `qwen2.5-coder:7b` or switch to `claude-cloud`. |
| CUDA allocation failure | Stop other GPU processes (`sudo systemctl stop llama-cline`), or use a smaller model. |
