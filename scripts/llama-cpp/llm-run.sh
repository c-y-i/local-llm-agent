#!/usr/bin/env bash
set -euo pipefail

# Run a model interactively via llama-cli.
#
# Usage:
#   llm-run.sh <model-name> [prompt]
#   llm-run.sh qwen3-4b "Explain TCP slow start in two sentences."
#
# <model-name> resolves to $LLM_MODELS_DIR/<model-name>.gguf.
# If [prompt] is omitted, drops into interactive mode.
#
# Env overrides:
#   LOCAL_LLM_AGENT_ROOT — repo root
#   LLAMA_CPP_ROOT       — sibling llama.cpp checkout/build
#   LLAMA_CPP_BIN        — llama-cli binary
#   LLM_MODELS_DIR       — model dir
#   N_GPU_LAYERS   — layers offloaded to GPU (default 999, llama.cpp clamps to model max)
#   N_CTX          — context size (default 4096)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

MODELS_DIR="$LLM_MODELS_DIR"
N_GPU_LAYERS="${N_GPU_LAYERS:-999}"
N_CTX="${N_CTX:-4096}"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <model-name> [prompt]" >&2
  echo "Available models:" >&2
  ls "$MODELS_DIR"/*.gguf 2>/dev/null | xargs -n1 basename | sed 's/\.gguf$//' | sed 's/^/  /' >&2 || true
  exit 1
fi

name="$1"
shift
model="${MODELS_DIR}/${name}.gguf"

if [[ ! -f "$model" ]]; then
  echo "Model file not found: $model" >&2
  exit 1
fi

if [[ ! -x "$LLAMA_CPP_BIN" ]]; then
  echo "llama-cli not found or not executable: $LLAMA_CPP_BIN" >&2
  echo "Did you build llama.cpp? See ${LOCAL_LLM_AGENT_ROOT}/docs/setup.md" >&2
  exit 1
fi

if [[ $# -eq 0 ]]; then
  exec "$LLAMA_CPP_BIN" -m "$model" -ngl "$N_GPU_LAYERS" -c "$N_CTX" -cnv
else
  exec "$LLAMA_CPP_BIN" -m "$model" -ngl "$N_GPU_LAYERS" -c "$N_CTX" -no-cnv -p "$*"
fi
