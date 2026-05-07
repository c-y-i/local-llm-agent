#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

# Pre-load a model into VRAM with extended keep-alive, so the first Cline turn
# isn't a cold load. Run this once before opening Cline; the model stays warm
# for KEEP_ALIVE (default 10m) after each request.
#
# Usage:
#   ./warmup_for_cline.sh                       # default: qwen-coder-cline, 10m
#   MODEL=qwen2.5-coder:3b ./warmup_for_cline.sh
#   KEEP_ALIVE=30m ./warmup_for_cline.sh

MODEL="${MODEL:-qwen-coder-cline}"
KEEP_ALIVE="${KEEP_ALIVE:-10m}"
HOST="${OLLAMA_HOST:-127.0.0.1:11434}"

if ! curl -fsS "http://${HOST}/api/tags" >/dev/null; then
  echo "Ollama API is not reachable at ${HOST}."
  echo "Run ${LOCAL_LLM_AGENT_ROOT}/scripts/ollama/serve.sh first."
  exit 1
fi

if ! curl -fsS "http://${HOST}/api/tags" | grep -q "\"${MODEL}"; then
  echo "Model '${MODEL}' is not installed."
  echo "Available models:"
  curl -s "http://${HOST}/api/tags" | python3 -c 'import json,sys; print("\n".join("  - "+m["name"] for m in json.load(sys.stdin)["models"]))'
  echo
  echo "If '${MODEL}' is a personality, build it first:"
  echo "  python3 ${LOCAL_LLM_AGENT_ROOT}/tuning/build.py ${MODEL}"
  exit 1
fi

echo "Warming up ${MODEL} with keep_alive=${KEEP_ALIVE}..."

# Send a tiny generate request with extended keep_alive so Ollama loads the
# model into VRAM and holds it. Subsequent calls within KEEP_ALIVE skip load.
curl -fsS "http://${HOST}/api/generate" -d "{
  \"model\": \"${MODEL}\",
  \"prompt\": \"ready\",
  \"stream\": false,
  \"keep_alive\": \"${KEEP_ALIVE}\",
  \"options\": {\"num_predict\": 1, \"temperature\": 0.0}
}" >/dev/null

echo "Loaded. Model held warm for ${KEEP_ALIVE} after each request."
echo
echo "Loaded model status:"
ollama ps
echo
echo "You can now point Cline at:"
echo "  Provider:  Ollama"
echo "  Base URL:  http://${HOST}"
echo "  Model:     ${MODEL}"
