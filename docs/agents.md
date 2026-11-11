# Agent Compatibility

English | [简体中文](agents.zh-CN.md)

## Tested

The following paths were tested locally on an RTX 3050 Laptop GPU with 6 GB
VRAM:

| Agent | llama.cpp | Ollama | Verified |
|---|---|---|---|
| Claude Code | Anthropic Messages API | Compatibility proxy | Yes |
| Codex CLI | OpenAI Responses API | Built-in integration | Yes |
| Hermes Agent | OpenAI Chat Completions | Native | Yes |

The shared end-to-end test used official Qwen3.5-4B Q4_K_M on llama.cpp.
Hermes was also verified with official Qwen3.5-2B and large context windows.

## Direct Commands

```bash
claude-local
codex-local
hermes-local
```

These commands:

- activate the managed virtualenv automatically;
- work from any project directory;
- preserve the caller's working directory;
- reuse an active local model;
- otherwise start the preferred installed llama.cpp model in the background;
- wait for the model server to become healthy before launching the agent.

Background llama.cpp logs are written to `$LLM_ROOT/run/llama-server.log`.

## Claude Code

llama.cpp exposes the Anthropic Messages API directly:

```bash
claude-local
```

For Ollama, `llm claude` starts the local Anthropic compatibility proxy
automatically. The proxy normalizes Claude Code's system-message layout and
uses the model server's context window.

## Codex CLI

```bash
codex-local
```

The Codex launcher configures a temporary custom provider using the Responses
API. Local Codex state is isolated under `$LLM_ROOT/codex-local`, so an
existing `~/.codex` configuration is not modified.

## Hermes Agent

```bash
hermes-local
```

Hermes uses a custom OpenAI-compatible provider and keeps state under
`$LLM_ROOT/hermes-local`.

For Ollama, prefer the agent-ready tags with explicit renderer/parser,
deterministic sampling, and 32K–64K context. See
[`models.md`](models.md#ollama-agent-tags). Native and OpenAI-compatible
tool-call responses were verified with `qwen3.5-2b-official` and the Huihui
2B agent tag.

### Context

Hermes reads the live llama.cpp context window from server metadata. Do not
set any of these in Hermes `config.yaml` for normal local use:

```yaml
model:
  context_length: 65536
  ollama_num_ctx: 65536
```

Hermes gives those values priority and may clamp a 256K server down to 64K.
`llm hermes` detects a conflicting setting and refuses to launch. Remove one
with:

```bash
HERMES_HOME=/home/cy/LLM/hermes-local \
  hermes config unset model.context_length
HERMES_HOME=/home/cy/LLM/hermes-local \
  hermes config unset model.ollama_num_ctx
```

Restart the Hermes session after changing context configuration.

### Lean Local Profile

The default Hermes prompt and toolsets can consume roughly 13K tokens before
project content. Skills are progressive: only the short index is always
present, while the full `SKILL.md` is read when used.

For 2B models, prefer a lean coding toolset and do not preload large skills:

```bash
hermes-local -t terminal,file,skills,todo,clarify
```

Disable or avoid browser, computer use, delegation, connections, image
generation, TTS, and memory tools during lean coding sessions. The 4B model
has more headroom but still benefits from a focused toolset.

## Safety

Agents can edit files and execute commands. Keep approval prompts enabled,
use Git, and work in a branch or disposable directory while evaluating a small
local model. Protocol compatibility does not guarantee reliable multi-step
tool use.
