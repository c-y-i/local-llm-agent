#!/usr/bin/env bash
set -euo pipefail

# Start llama-server with Cline-friendly settings.
# Uses model-specific context defaults because KV-cache size varies a lot by
# architecture, context length, quantization, and hardware tier. Does NOT inject
# a SYSTEM prompt — Cline sends its own elaborate system prompt with tool
# descriptions, so adding one here would conflict.
#
# Usage:
#   cline-server.sh                              # default model (qwen2.5-coder-3b)
#   cline-server.sh qwen3-4b                     # different shared GGUF
#   cline-server.sh qwen2.5-coder-3b 8081        # custom port
#
# Env overrides:
#   LOCAL_LLM_AGENT_ROOT  repo root
#   LLAMA_CPP_ROOT        sibling llama.cpp checkout/build
#   LLAMA_SERVER_BIN      llama-server binary
#   LLM_MODELS_DIR        model dir
#   N_GPU_LAYERS      999
#   N_CTX             model-specific default; set explicitly to override
#   N_PARALLEL        1
#   METRICS           1
#   TEMP              0.2
#   TOP_P             0.9
#   REPEAT_PENALTY    1.1
#   HOST              127.0.0.1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

MODELS_DIR="$LLM_MODELS_DIR"
N_GPU_LAYERS="${N_GPU_LAYERS:-999}"
N_PARALLEL="${N_PARALLEL:-1}"
METRICS="${METRICS:-1}"
TEMP="${TEMP:-0.2}"
TOP_P="${TOP_P:-0.9}"
REPEAT_PENALTY="${REPEAT_PENALTY:-1.1}"
HOST="${HOST:-127.0.0.1}"

name="${1:-qwen2.5-coder-3b}"
port="${2:-8080}"
model="${MODELS_DIR}/${name}.gguf"

if [[ -z "${N_CTX+x}" ]]; then
  case "$name" in
    qwen2.5-coder-3b)
      N_CTX=32768
      ;;
    llama3.2-3b|qwen3-1.7b)
      N_CTX=12288
      ;;
    qwen3-4b|phi4-mini)
      N_CTX=8192
      ;;
    *)
      N_CTX=8192
      ;;
  esac
fi

if [[ ! -x "$LLAMA_SERVER_BIN" ]]; then
  echo "llama-server not found: $LLAMA_SERVER_BIN" >&2
  exit 1
fi
if [[ ! -f "$model" ]]; then
  echo "Model file not found: $model" >&2
  echo "Available:" >&2
  ls "$MODELS_DIR"/*.gguf 2>/dev/null | xargs -n1 basename | sed 's/\.gguf$//; s/^/  /' >&2 || true
  exit 1
fi

if command -v ss >/dev/null 2>&1; then
  listener="$(ss -H -tlnp 2>/dev/null | awk -v p=":${port}" '$4 ~ p "$" {print; exit}')"
  if [[ -n "$listener" ]]; then
    echo "Port ${port} is already in use:" >&2
    echo "  $listener" >&2
    echo "Choose another port, or stop the process using ${HOST}:${port}." >&2
    exit 1
  fi
fi

# Warn if Ollama has a model loaded — VRAM is shared.
if command -v ollama >/dev/null 2>&1; then
  if ollama ps 2>/dev/null | awk 'NR>1{exit 0} END{exit 1}'; then
    echo "WARN: Ollama currently has a model loaded — VRAM may be tight." >&2
    echo "      Run 'curl -s http://127.0.0.1:11434/api/generate -d {\"model\":\"<tag>\",\"keep_alive\":0,\"prompt\":\".\"} >/dev/null'" >&2
    echo "      to unload, or use N_GPU_LAYERS=<lower> to partial-offload." >&2
    echo >&2
  fi
fi

echo "Cline ⇄ llama-server"
echo "  Model       : $model"
echo "  Endpoint    : http://${HOST}:${port}/v1"
echo "  GPU layers  : $N_GPU_LAYERS"
echo "  Context     : $N_CTX"
echo "  Parallel    : $N_PARALLEL"
echo "  Metrics     : $METRICS"
echo "  Temperature : $TEMP (server default; Cline can override per-call)"
echo "  Top-p       : $TOP_P"
echo "  Repeat pen. : $REPEAT_PENALTY"
echo
echo "In Cline (VS Code):"
echo "  Provider : OpenAI Compatible"
echo "  Base URL : http://${HOST}:${port}/v1"
echo "  API Key  : 114514"
echo "  Model ID : ${name}      (informational; llama-server only serves the loaded model)"
echo "  Context  : ${N_CTX}      (set Cline Context Window Size to match)"
echo

args=(
  "$LLAMA_SERVER_BIN"
  -m "$model"
  -ngl "$N_GPU_LAYERS"
  -c "$N_CTX"
  -np "$N_PARALLEL"
  --temp "$TEMP"
  --top-p "$TOP_P"
  --repeat-penalty "$REPEAT_PENALTY"
  --host "$HOST"
  --port "$port"
)

if [[ "$METRICS" != "0" && "$METRICS" != "false" ]]; then
  args+=(--metrics)
fi

exec "${args[@]}"
