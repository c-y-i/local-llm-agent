#!/usr/bin/env bash
set -euo pipefail

# Start Strata with its OpenAI- and Anthropic-compatible API.
#
# Usage:
#   STRATA_FAMILY=qwen STRATA_MODEL=q2_0 ./scripts/strata/serve.sh
#   STRATA_FAMILY=qwen36 STRATA_MODEL=UD-Q4_K_XL ./scripts/strata/serve.sh
#
# Strata downloads and manages its own model packs. Check a plan first with:
#   strata launch --family "$STRATA_FAMILY" --model "$STRATA_MODEL" --plan

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

family="${STRATA_FAMILY:-qwen}"
model="${1:-${STRATA_MODEL:-}}"
port="${2:-${STRATA_PORT}}"
host="${STRATA_HOST}"

if [[ -z "$model" ]]; then
  echo "Usage: $0 [model] [port]" >&2
  echo "Set STRATA_FAMILY and STRATA_MODEL, or pass a model name." >&2
  exit 1
fi

if ! command -v "$STRATA_BIN" >/dev/null 2>&1; then
  echo "Strata was not found: $STRATA_BIN" >&2
  echo "Install it from https://github.com/Niko1221/Strata" >&2
  exit 1
fi

args=(
  launch
  --family "$family"
  --model "$model"
  --host "$host"
  --port "$port"
  --data-dir "$STRATA_MODELS_DIR"
  --yes
  --no-tui
)

if [[ -n "${STRATA_API_KEY:-}" ]]; then
  args+=(--api-key-env STRATA_API_KEY)
else
  args+=(--no-api-key)
fi
if [[ -n "${STRATA_EXTRA_ARGS:-}" ]]; then
  read -r -a extra_args <<<"$STRATA_EXTRA_ARGS"
  args+=("${extra_args[@]}")
fi

echo "Starting Strata model ${family}/${model} on http://${host}:${port}"
echo "  OpenAI:    http://${host}:${port}/v1"
echo "  Anthropic: http://${host}:${port}/v1/messages"
echo
exec "$STRATA_BIN" "${args[@]}"
