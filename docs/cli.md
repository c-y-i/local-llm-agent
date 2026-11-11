# llm CLI

English | [简体中文](cli.zh-CN.md)

`llm` is the single entry point for paths, diagnostics, engine setup, model
listing, server launch, and agent launch.

## Everyday Flow

Start the interactive menu:

```bash
llm
```

It presents three separate concepts:

- **Model/backend:** choose which engine and model to run.
- **Agent:** choose Claude Code, Codex CLI, or Hermes after a model is running.
- **Runtime:** inspect status, paths, and installation health.

Choose a backend and existing model interactively:

```bash
llm setup
llm start
```

In another terminal, choose an agent for the running model:

```bash
llm agent
```

The CLI fills in the backend, served model ID, endpoint, and protocol. Explicit
arguments remain available for scripts.

## Install

```bash
./scripts/setup/install-llm.sh
source .venv/bin/activate
llm --version
```

The installer links `~/.local/bin/llm` to this repository. Ensure
`~/.local/bin` is on `PATH`. The virtualenv is intentionally explicit:
activate it in every new shell before using `llm`.

It also installs direct local-agent commands:

```bash
claude-local
codex-local
hermes-local
```

These commands call `llm agent <name>` internally, so they use the same
backend/model selection and configuration isolation. `llm` and the `*-local`
commands coexist.

## Storage

```bash
llm paths
llm paths --json
llm config
llm config --init
```

The default layout is:

```text
~/LLM/
  models/
  models/strata/
  ollama/
  llama.cpp/
  huggingface/
  strata/
  .venv/                # required managed virtualenv
  run/
```

Override everything with `LLM_ROOT`, or override individual directories in
the repository's ignored `.env` file. See `.env.example`.

## Diagnose

```bash
llm doctor
llm status
llm status --json
llm models
llm models --json
```

`doctor` checks commands, writability, and backend reachability. `status`
probes llama.cpp, vLLM, Strata, and Ollama at their configured URLs.

## Build And Install

```bash
llm build llama-cpp --dry-run
llm build llama-cpp
llm build llama-cpp --cuda OFF   # force CPU-only
llm build llama-cpp --cuda ON

llm install vllm                 # ~/LLM/.venv
llm install ollama
```

`llm install strata` prints the upstream installation path because Strata
uses its own release/install process.

## Start A Model

```bash
llm start
llm start llama-cpp qwen3.5-4b
llm start llama-cpp qwen3.5-4b --context 32768
llm start vllm Qwen/Qwen3.5-4B
llm start strata q2_0 --family qwen
llm start ollama
```

Servers run in the foreground. Use a terminal multiplexer or a service manager
when they must stay active.

`llm serve` remains an alias for `llm start`.

## Choose An Agent

```bash
llm agent
llm agent claude
llm agent codex
llm agent hermes
```

`llm agent` reads the running backend and served model automatically. If
multiple backends are running, it asks which one to use.

Use `--` before arbitrary agent CLI options:

```bash
llm agent hermes --model qwen3.5-4b-official:latest -- \
  -q "Reply with exactly READY" --oneshot -Q
```

## Claude Code

```bash
llm claude --backend llama-cpp --model qwen3.5-4b
llm claude --backend vllm --model Qwen3.5-4B
llm claude --backend strata --model q2_0
llm claude --backend ollama --model qwen2.5-coder:3b
```

Omit `--backend` to auto-detect a running backend. Arguments after the
recognized `llm` options are passed to Claude Code:

```bash
llm claude --backend llama-cpp --model qwen3.5-4b -p "Explain this repo"
```

## Codex CLI

Codex custom providers use the OpenAI Responses API:

```bash
llm codex --backend llama-cpp --model qwen3.5-4b
llm codex --backend vllm --model Qwen3.5-4B
llm codex --backend strata --model q2_0
llm codex --backend ollama --model qwen3.5:4b
```

For llama.cpp, vLLM, and Strata, `llm codex` supplies a temporary provider
configuration using `/v1/responses` and sets a conservative 32K context. For
Ollama it uses Codex's built-in local provider. Change the context with
`--context`.

Arguments after the recognized options are passed through to Codex:

```bash
llm codex --backend llama-cpp --model qwen3.5-4b exec "Fix the failing test"
```

## Hermes Agent

Hermes uses an OpenAI-compatible custom endpoint:

```bash
llm hermes --backend llama-cpp --model qwen3.5-4b
llm hermes --backend vllm --model Qwen3.5-4B
llm hermes --backend strata --model q2_0
llm hermes --backend ollama --model qwen3.5:4b
```

`llm hermes` sets `OPENAI_BASE_URL`, `OPENAI_API_KEY`, the provider, and the
model without writing repository files.
