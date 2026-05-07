#!/usr/bin/env bash
set -euo pipefail

# Remove a shared model from both Ollama and the shared model directory.
#
# Usage:
#   remove-model.sh <ollama-tag> [friendly-name]
#
# If [friendly-name] is omitted, derived as in pull-and-share.sh.
# Always asks for confirmation before deleting the GGUF.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

LLM_MODELS="$LLM_MODELS_DIR"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <ollama-tag> [friendly-name]" >&2
  exit 1
fi

tag="$1"
friendly="${2:-}"
if [[ -z "$friendly" ]]; then
  derived="$(echo "$tag" | sed 's|/|-|g; s|:|-|g')"
  derived="${derived%-latest}"
  friendly="${derived}.gguf"
fi
case "$friendly" in *.gguf) ;; *) friendly="${friendly}.gguf" ;; esac
gguf="${LLM_MODELS}/${friendly}"

echo "Will remove:"
echo "  Ollama tag : $tag"
echo "  GGUF file  : $gguf"
read -r -p "Proceed? [y/N] " ans
case "${ans,,}" in
  y|yes) ;;
  *) echo "Aborted."; exit 1 ;;
esac

if ollama list 2>/dev/null | awk 'NR>1{print $1}' | grep -Fxq -e "$tag" -e "${tag}:latest"; then
  echo "==> ollama rm $tag"
  ollama rm "$tag"
fi

if [[ -e "$gguf" ]]; then
  echo "==> rm $gguf"
  rm -- "$gguf"
fi

echo "Done."
