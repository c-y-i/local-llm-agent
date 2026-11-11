# Using Strata

English | [简体中文](usage-strata.zh-CN.md)

Strata is a specialized inference engine that streams mixture-of-experts
models across GPU memory, system RAM, and SSD. It is for running models much
larger than the available VRAM, not for making a small model faster.

Install Strata separately from its upstream project:

<https://github.com/Niko1221/Strata>

Confirm that `strata` is available:

```bash
strata --version
strata launch --help
```

## Plan Before Downloading

Strata model packs can be tens to hundreds of gigabytes. Always inspect the
launch plan first:

```bash
strata launch --family qwen --model q2_0 --plan
```

The plan reports RAM, VRAM, disk, and backend compatibility. Do not start a
download until the plan fits the machine.

## Serve Through This Repo

Qwen3.8-Flash-Next:

```bash
STRATA_FAMILY=qwen STRATA_MODEL=q2_0 ./scripts/strata/serve.sh
```

Qwen3.6-35B-A3B:

```bash
STRATA_FAMILY=qwen36 STRATA_MODEL=UD-Q4_K_XL ./scripts/strata/serve.sh
```

The wrapper defaults to `127.0.0.1:8082` to avoid colliding with llama.cpp on
port 8080.

| Variable | Default | Purpose |
|---|---|---|
| `STRATA_FAMILY` | `qwen` | Strata model family |
| `STRATA_MODEL` | unset | Model pack name |
| `STRATA_PORT` | `8082` | Server port |
| `STRATA_HOST` | `127.0.0.1` | Bind address |
| `STRATA_API_KEY` | unset | Enables API-key authentication |
| `STRATA_MODELS_DIR` | `$LLM_ROOT/models/strata` | Model download directory |
| `STRATA_EXTRA_ARGS` | unset | Additional space-separated launch flags |

When `STRATA_API_KEY` is unset, the wrapper uses `--no-api-key` and expects a
loopback-only bind.

## Endpoints

```text
OpenAI:    http://127.0.0.1:8082/v1
Anthropic: http://127.0.0.1:8082
Messages:  http://127.0.0.1:8082/v1/messages
Models:    http://127.0.0.1:8082/v1/models
```

## Claude Code

```bash
./scripts/claude/claude-local.sh --backend strata --model strata
```

If Strata returns a different model ID from `/v1/models`, use that ID.

## Hardware Note

Strata is a poor efficiency choice on a laptop with 6 GB VRAM and 13 GB usable
RAM. Its smallest Qwen3.8 pack needs roughly 27.6 GB of combined VRAM and RAM;
the Qwen3.6 4-bit plan expects around 32 GB of RAM. Low-memory mode can stream
experts from the SSD, but the project explicitly warns that this is much
slower. Use Strata only when capability matters more than latency.
