#!/usr/bin/env bash
set -euo pipefail

# List all GGUF files in the shared model directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

MODELS_DIR="$LLM_MODELS_DIR"

if [[ ! -d "$MODELS_DIR" ]]; then
  echo "Models dir not found: $MODELS_DIR" >&2
  exit 1
fi

shopt -s nullglob
gguf_files=("$MODELS_DIR"/*.gguf)
shopt -u nullglob

if [[ ${#gguf_files[@]} -eq 0 ]]; then
  echo "No .gguf files in $MODELS_DIR"
  exit 0
fi

printf '%-40s  %10s  %s\n' "NAME" "SIZE" "PATH"
for f in "${gguf_files[@]}"; do
  name="$(basename "$f" .gguf)"
  size="$(du -h "$f" | cut -f1)"
  printf '%-40s  %10s  %s\n' "$name" "$size" "$f"
done
