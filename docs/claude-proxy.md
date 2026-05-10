# Claude Code Proxy Internals

English | [简体中文](claude-proxy.zh-CN.md)

This repo uses `scripts/ollama/anthropic-proxy.py` to let Claude Code talk to
local Ollama models.

Claude Code sends Anthropic Messages API requests. Ollama does not implement
that API, so the proxy translates:

```text
Claude Code -> Anthropic-compatible proxy :4000 -> Ollama :11434
```

## What The Proxy Does

The proxy has three separate jobs.

1. API translation

   It converts Claude Code's `/v1/messages` requests into Ollama's
   OpenAI-compatible `/v1/chat/completions` requests, then converts the answer
   back into Anthropic Messages format.

2. Thinking/reasoning cleanup

   Claude Code sends Anthropic `thinking` parameters. Local Ollama models either
   reject that parameter or return reasoning fields that LiteLLM/Claude Code do
   not accept. The proxy drops the Anthropic-only thinking request before
   forwarding to Ollama and strips leaked reasoning text from responses.

3. Local-model guardrails

   Small local models often emit JSON-looking text instead of real Claude Code
   `tool_use` blocks. The proxy handles a few common failure modes:

   - placeholder paths such as `/path/to/your/file.txt`;
   - fake `{"name": "...", "arguments": ...}` tool blobs;
   - Qwen3 `<think>...</think>` text leaks;
   - simple greetings that should be plain text, not tools.

## Experimental Intent Router

There is one deliberately pragmatic piece: the proxy has a small intent router
for obvious filesystem questions such as:

```text
what path are we in?
what is in /home/cy/Downloads?
what folders are in here?
```

That is why phrases appear in the code. The router exists because
`qwen2.5-coder:3b` was repeatedly describing or inventing tool calls instead of
emitting valid Claude Code tool calls. For those narrow filesystem prompts, the
proxy can return a direct Claude Code `tool_use` response such as `Bash pwd` or
`LS /some/path`.

This is not general natural-language understanding. It is a small compatibility
shim for local-model testing. Keep it conservative and documented.

Disable it if you want the proxy to only translate API formats:

```bash
CLAUDE_PROXY_ENABLE_INTENT_ROUTER=0 python3 scripts/ollama/anthropic-proxy.py
```

For the systemd service, edit the unit generated from
`systemd/litellm-proxy.service.in`:

```ini
Environment=CLAUDE_PROXY_ENABLE_INTENT_ROUTER=0
```

Then reinstall/restart:

```bash
./scripts/ollama/install-claude-proxy-service.sh
sudo systemctl restart litellm-proxy
```

## Service Naming

The service is still named `litellm-proxy.service` for compatibility with older
notes and shell workflows. It no longer runs LiteLLM. The installed unit runs:

```text
/usr/bin/python3 /media/data/LLM/scripts/ollama/anthropic-proxy.py
```

Use either installer name:

```bash
./scripts/ollama/install-claude-proxy-service.sh
./scripts/ollama/install-litellm-service.sh
```

Both install the same service.

## Known Limits

- Tool use remains model-dependent. The proxy can patch narrow failures, but it
  cannot make a small local model behave like Claude.
- Qwen3 models can spend the output budget on reasoning and return empty
  content. Prefer `qwen2.5-coder:3b` on this machine.
- If the model keeps inventing tool calls, use a stronger model or switch to
  `claude-cloud`.
