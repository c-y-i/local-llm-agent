#!/usr/bin/env bash
set -euo pipefail

# Start vLLM's OpenAI- and Anthropic-compatible API server.
#
# Usage:
#   serve.sh <hugging-face-model-or-path> [port]
#   serve.sh Qwen/Qwen3.5-4B 8000
#
# vLLM loads Hugging Face safetensors/AWQ/GPTQ weights, not GGUF files.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

model="${1:-${VLLM_MODEL:-}}"
port="${2:-${VLLM_PORT}}"
host="${VLLM_HOST}"
tool_parser="${VLLM_TOOL_CALL_PARSER:-qwen3_coder}"
served_name="${VLLM_SERVED_MODEL_NAME:-}"

if [[ -z "$model" ]]; then
  echo "Usage: $0 <hugging-face-model-or-path> [port]" >&2
  echo "Or set VLLM_MODEL." >&2
  exit 1
fi

if [[ -z "$served_name" ]]; then
  served_name="$(basename "$model")"
  served_name="${served_name//[^A-Za-z0-9_.-]/-}"
fi

if command -v "$VLLM_BIN" >/dev/null 2>&1; then
  vllm_cmd="$VLLM_BIN"
elif [[ -x "$VLLM_BIN" ]]; then
  vllm_cmd="$VLLM_BIN"
else
  echo "vLLM was not found: $VLLM_BIN" >&2
  echo "Install it with: python3 -m pip install vllm" >&2
  exit 1
fi

args=(
  serve "$model"
  --host "$host"
  --port "$port"
  --served-model-name "$served_name"
)

if [[ "$tool_parser" != "none" && "$tool_parser" != "0" ]]; then
  args+=(--enable-auto-tool-choice --tool-call-parser "$tool_parser")
fi
[[ -n "${VLLM_REASONING_PARSER:-}" ]] && args+=(--reasoning-parser "$VLLM_REASONING_PARSER")
[[ -n "${VLLM_MAX_MODEL_LEN:-}" ]] && args+=(--max-model-len "$VLLM_MAX_MODEL_LEN")
[[ -n "${VLLM_GPU_MEMORY_UTILIZATION:-}" ]] && args+=(--gpu-memory-utilization "$VLLM_GPU_MEMORY_UTILIZATION")
if [[ -n "${VLLM_EXTRA_ARGS:-}" ]]; then
  read -r -a extra_args <<<"$VLLM_EXTRA_ARGS"
  args+=("${extra_args[@]}")
fi

echo "Serving ${model} with vLLM on http://${host}:${port}"
echo "  Model ID: ${served_name}"
echo "  OpenAI:   http://${host}:${port}/v1"
echo "  Anthropic: http://${host}:${port}/v1/messages"
echo
exec "$vllm_cmd" "${args[@]}"
