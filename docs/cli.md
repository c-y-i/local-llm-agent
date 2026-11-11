# llm CLI

English | [简体中文](cli.zh-CN.md)

`llm` is the control tool for model storage, llama.cpp and Ollama, runtime
status, and agent launch.

## Install

```bash
./scripts/setup/install-llm.sh
source .venv/bin/activate
llm --version
```

`llm` requires the managed virtualenv. The installed `claude-local`,
`codex-local`, and `hermes-local` commands activate it automatically.

## Main Menu

```bash
llm
```

The header reports the loaded model and reachable services separately. An
Ollama daemon without a loaded model is shown as `ready (idle)`.

The action order is stable:

1. Run a model
2. Browse installed models
3. Open a coding agent
4. Stop the active model
5. Show runtime and backend status
6. View active backend logs
7. Manage backends and installations
8. Run diagnostics
9. Show storage locations
10. Quit

## Run A Model

Start a backend and choose an installed model:

```bash
llm start
```

Explicit llama.cpp launch:

```bash
llm start llama-cpp qwen3.5-4b-official-Q4_K_M
llm start llama-cpp qwen3.5-4b-official-Q4_K_M --context 65536
llm start llama-cpp qwen3.5-4b-official-Q4_K_M --gpu-layers 24
```

Interactive llama.cpp launches show a context-window picker. Models are shown
with their installed size and sorted smallest-first. Qwen3.5-4B is marked as
the recommended default when present.

Warm an installed Ollama model:

```bash
llm start ollama qwen3.5-4b-official:latest
```

Ollama runs as a background daemon. In an interactive terminal,
`llm start ollama` asks for a context window, loads the selected model, and
then follows the daemon log in the foreground. Press `Ctrl+C` to return; the
model stays loaded. Launch the agent separately with `claude-local`,
`codex-local`, or `hermes-local`.

You can bypass the picker:

```bash
llm start ollama qwen3.5-2b-official:latest --context 131072
OLLAMA_NUM_CTX=131072 llm start ollama
```

Changing the context unloads and reloads the Ollama model, updates the tag's
`num_ctx`, and invalidates Hermes's cached context entry. Restart an already
running Hermes session after changing the context.

If Ollama is not running, `llm start ollama` starts it as a managed background
daemon with output written to `$LLM_ROOT/run/ollama.log`.

Servers normally run in the foreground. Direct local-agent commands can start
the preferred llama.cpp model in the background when no model is active.

If llama.cpp is already serving a model on port 8080, `llm start` offers to
replace it. The tracked background server can also be stopped directly:

```bash
llm stop
```

Only one inference engine is allowed at a time. Starting llama.cpp stops the
Ollama daemon first; starting Ollama stops any llama.cpp server first. Direct
agent auto-start follows the same rule.

## Installed Models

```bash
llm models
llm models --backend llama-cpp
llm models --sort name
llm models --json
```

Sorting by installed size, smallest first, is automatic. `--sort name` switches
to alphabetical order.

## Status And Diagnostics

```bash
llm status
llm status --json
llm doctor
llm logs
llm logs --backend ollama --lines 100
llm logs --backend llama-cpp --follow
```

`status` distinguishes:

- `active`: a model is loaded and serving requests.
- `ready`: a service is reachable but has no loaded model.
- `offline`: the endpoint is unreachable.

`doctor` checks commands, writability, storage, and backend reachability.
`logs` tails the active backend's managed log; use `--follow` for a live stream.

## Agents

From any project directory:

```bash
claude-local
codex-local
hermes-local
```

These commands activate the managed environment, start the preferred installed
model when necessary, and preserve the caller's working directory.

The equivalent generic flow is:

```bash
llm agent
llm agent claude
llm agent codex
llm agent hermes
```

Explicit launch forms are also available once a model is active:

```bash
llm claude --backend llama-cpp --model qwen3.5-4b-official-Q4_K_M
llm codex --backend llama-cpp --model qwen3.5-4b-official-Q4_K_M
llm hermes --backend llama-cpp --model qwen3.5-4b-official-Q4_K_M
```

Pass agent-specific options after `--`:

```bash
llm agent hermes -- -q "Reply with READY" --oneshot -Q
```

## Paths And Configuration

```bash
llm paths
llm paths --json
llm config
llm config --init
```

The default data root is `~/LLM`. Set `LLM_ROOT` or individual paths in the
repository's ignored `.env` file. Model files are never part of the repository.

## Build And Install Backends

```bash
llm build llama-cpp --dry-run
llm build llama-cpp
llm install ollama
```

llama.cpp is the primary tested backend. Ollama is supported as a secondary
backend and shared model store. vLLM and Strata are deferred for the current
hardware workflow.
