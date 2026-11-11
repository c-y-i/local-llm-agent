#!/usr/bin/env bash
set -euo pipefail

# Start llama-server (OpenAI-compatible HTTP API) for a given model.
#
# Usage:
#   llm-serve.sh <model-name> [port]
#   llm-serve.sh qwen2.5-coder-3b 8080
#
# Default port is 8080. The server exposes:
#   http://127.0.0.1:<port>/v1/chat/completions
#   http://127.0.0.1:<port>/v1/completions
#   http://127.0.0.1:<port>/v1/models
#
# Env overrides:
#   LOCAL_LLM_AGENT_ROOT — repo root
#   LLAMA_CPP_ROOT       — external llama.cpp checkout/build
#   LLAMA_SERVER_BIN     — llama-server binary
#   LLM_MODELS_DIR       — model dir
#   N_GPU_LAYERS     — layers offloaded to GPU (default 999)
#   N_CTX            — context size (default 8192)
#   JINJA            — enable model chat templates for tool calling (default 1)
#   HOST             — bind host (default 127.0.0.1)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

MODELS_DIR="$LLM_MODELS_DIR"
N_GPU_LAYERS="${N_GPU_LAYERS:-999}"
N_CTX="${N_CTX:-8192}"
HOST="${HOST:-${LLAMA_CPP_HOST}}"
JINJA="${JINJA:-1}"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <model-name> [port]" >&2
  echo "Available models:" >&2
  ls "$MODELS_DIR"/*.gguf 2>/dev/null | xargs -n1 basename | sed 's/\.gguf$//' | sed 's/^/  /' >&2 || true
  exit 1
fi

name="$1"
port="${2:-${LLAMA_CPP_PORT}}"
model="${MODELS_DIR}/${name}.gguf"

if [[ ! -f "$model" ]]; then
  echo "Model file not found: $model" >&2
  exit 1
fi

if [[ ! -x "$LLAMA_SERVER_BIN" ]]; then
  echo "llama-server not found or not executable: $LLAMA_SERVER_BIN" >&2
  exit 1
fi

args=(
  "$LLAMA_SERVER_BIN"
  -m "$model"
  --alias "$name"
  -ngl "$N_GPU_LAYERS"
  -c "$N_CTX"
  --host "$HOST"
  --port "$port"
)
if [[ "$JINJA" != "0" && "$JINJA" != "false" ]]; then
  args+=(--jinja)
fi
[[ -n "${LLAMA_SERVER_API_KEY:-}" ]] && args+=(--api-key "$LLAMA_SERVER_API_KEY")

echo "Serving ${name} on http://${HOST}:${port} (ngl=${N_GPU_LAYERS}, ctx=${N_CTX})"
echo "Claude Code: ANTHROPIC_BASE_URL=http://${HOST}:${port}"
exec "${args[@]}"
