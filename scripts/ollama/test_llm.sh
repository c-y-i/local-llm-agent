#!/usr/bin/env bash
set -euo pipefail

# Quick local inference test through Ollama's local HTTP API.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

EXPECTED_MODELS="$OLLAMA_MODELS"
MODEL="${MODEL:-qwen3:1.7b}"
PROMPT="Reply with one short sentence proving local inference works."

SERVICE_ENV="$(systemctl show ollama --property=Environment --value 2>/dev/null || true)"
if [[ "$SERVICE_ENV" != *"OLLAMA_MODELS=${EXPECTED_MODELS}"* ]]; then
  echo "Ollama systemd model path is not set to the current folder."
  echo "Expected: OLLAMA_MODELS=${EXPECTED_MODELS}"
  echo "Current: ${SERVICE_ENV:-<unset>}"
  echo
  echo "Run ${LOCAL_LLM_AGENT_ROOT}/scripts/ollama/serve.sh first."
  exit 1
fi

HTTP_CODE="$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:11434/api/tags || true)"
if [[ "$HTTP_CODE" != "200" ]]; then
  echo "Ollama API is not healthy at 127.0.0.1:11434 (HTTP ${HTTP_CODE})."
  echo "Run ${LOCAL_LLM_AGENT_ROOT}/scripts/ollama/serve.sh first."
  exit 1
fi

JSON_RESPONSE=$(curl -fsS http://127.0.0.1:11434/api/generate -d "{\"model\":\"${MODEL}\",\"prompt\":\"${PROMPT}\",\"stream\":false}")
TEXT_RESPONSE=$(printf '%s' "$JSON_RESPONSE" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("response",""))')

echo "Model: ${MODEL}"
echo "Prompt: $PROMPT"
echo "Response: $TEXT_RESPONSE"
