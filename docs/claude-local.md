# claude-local Launcher

`claude-local` is the day-to-day launcher for Claude Code against local Ollama
models.

It wraps the real `claude` command with the local proxy environment:

```bash
ANTHROPIC_BASE_URL=http://localhost:4000
ANTHROPIC_AUTH_TOKEN=ollama
```

The launcher script is:

```bash
scripts/ollama/claude-local.sh
```

The shell shortcut in `~/.bashrc` should call that script:

```bash
function claude-local() {
  /media/data/LLM/scripts/ollama/claude-local.sh "$@"
}
```

## Model Picker

Run `claude-local` with no `--model` argument to open the picker:

```bash
claude-local
```

<img src="claude_local_menu.png" alt="claude-local model picker showing loaded Ollama models first" width="720">

The picker reads:

- `ollama ps` for currently loaded models;
- `ollama list` for installed models.

Loaded models are listed first and marked `[RUNNING]`. If no model is loaded,
preferred Claude Code models are shown first:

1. `qwen2.5-coder:3b`
2. `qwen2.5-coder:7b`
3. `llama3.2:3b`
4. `phi4-mini:latest`

Interactive controls:

| Key | Action |
|---|---|
| Up / Down | Move selection |
| `j` / `k` | Move selection |
| Enter | Select highlighted model |
| number | Select that numbered model |
| `q` | Quit |

In non-interactive shells, the launcher falls back to selecting option `1`.

## Examples

Open the picker:

```bash
claude-local
```

Skip the picker:

```bash
claude-local --model qwen2.5-coder:3b
```

Pick a model first, then run a one-shot prompt:

```bash
claude-local -p "Reply with exactly: ready"
```

Pass a custom system prompt for one session:

```bash
CLAUDE_LOCAL_SYSTEM_PROMPT="Be concise and prefer tools for filesystem questions." claude-local
```

## Requirements

Ollama must be reachable on port 11434:

```bash
./scripts/ollama/serve.sh
```

The Claude Code proxy must be running on port 4000:

```bash
sudo systemctl start litellm-proxy
curl -s http://localhost:4000/health
```

For proxy internals, see [`claude-proxy.md`](claude-proxy.md).

## Current Recommendation

Use `qwen2.5-coder:3b` first. It fits this machine and is the most reliable
local Claude Code model tested so far.

Try `qwen2.5-coder:7b` for harder code tasks if there is enough free VRAM.
Avoid `qwen3:*` for Claude Code unless you are testing reasoning behavior; it
can spend the response budget on hidden reasoning and return empty content.
