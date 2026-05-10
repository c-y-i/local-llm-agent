# Tuning

English | [简体中文](tuning.zh-CN.md)

Tuning here means changing runtime parameters, Ollama Modelfiles, or reusable personality definitions.

## Common Parameters

| Parameter | Typical range | Notes |
|---|---:|---|
| `temperature` | `0.2` to `0.9` | Lower for code/factual work, higher for creative chat. |
| `top_p` | `0.85` to `0.95` | Nucleus sampling cutoff. |
| `repeat_penalty` | `1.0` to `1.3` | `1.1` is a mild anti-loop nudge. |
| `num_ctx` / `N_CTX` | model/GPU dependent | Bigger context costs more KV-cache memory. |
| `num_predict` / `max_tokens` | task dependent | Keep Cline large enough to finish tool calls. |

## llama.cpp Flags

```bash
N_CTX=8192 TEMP=0.2 TOP_P=0.9 REPEAT_PENALTY=1.1 \
  ./scripts/llama-cpp/cline-server.sh qwen2.5-coder-3b
```

## Ollama Per-Call Options

```bash
curl -s http://127.0.0.1:11434/api/generate -d '{
  "model": "qwen2.5-coder:3b",
  "prompt": "Write a one-line shell command.",
  "stream": false,
  "options": {
    "temperature": 0.2,
    "top_p": 0.9,
    "num_predict": 128,
    "repeat_penalty": 1.1
  }
}'
```

## Personality Modelfiles

Personality definitions live in:

```text
tuning/personalities.py
```

Generate/rebuild:

```bash
cd tuning
python3 build.py qwen-coder-cline
```

Generated Modelfiles go to:

```text
modelfiles/personalities/
```

The builder uses `LOCAL_LLM_AGENT_ROOT` when set, otherwise it discovers the repo root from its own location.

## Compare Models

```bash
cd tuning
python3 compare.py --temp 0.2 "Refactor this loop..." qwen2.5-coder:3b qwen-coder-cline
```

## Cline Notes

Cline can include a large system prompt and tool descriptions before the user message. Use the context value printed by `cline-server.sh`; do not assume every model can fit the same context on every GPU.
