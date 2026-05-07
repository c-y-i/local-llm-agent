#!/usr/bin/env bash
set -euo pipefail

# Re-create symlinks in Ollama's CAS for any local GGUF whose manifest is
# present in Ollama but whose CAS blob path is missing or wrong.
#
# Use this after re-pulling a model that was previously shared, when ollama
# wrote a fresh blob to the CAS path that used to be a symlink.
#
# Usage:
#   relink-to-ollama.sh                    # scan all manifests
#   relink-to-ollama.sh qwen3:4b           # only this tag

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

CAS="${OLLAMA_MODELS}/blobs"
MANIFESTS="${OLLAMA_MODELS}/manifests/registry.ollama.ai"
LLM_MODELS="$LLM_MODELS_DIR"

scan_one() {
  local manifest="$1"
  local rel="${manifest#${MANIFESTS}/}"
  local digest
  digest="$(python3 -c '
import json, sys
m = json.load(open(sys.argv[1]))
for layer in m["layers"]:
    if layer["mediaType"] == "application/vnd.ollama.image.model":
        print(layer["digest"].replace(":", "-")); sys.exit(0)
' "$manifest")"
  [[ -z "$digest" ]] && return 0
  local cas="${CAS}/${digest}"

  # Find a matching friendly file in the local GGUF model directory.
  if [[ -L "$cas" && -e "$cas" ]]; then
    return 0  # already symlinked and valid
  fi
  local cas_size=0
  [[ -f "$cas" ]] && cas_size=$(stat -c '%s' "$cas")

  local match=""
  for f in "$LLM_MODELS"/*.gguf; do
    [[ -f "$f" ]] || continue
    local fsize=$(stat -c '%s' "$f")
    if [[ "$fsize" == "$cas_size" || "$cas_size" == "0" ]]; then
      # Without re-hashing every blob, prefer name-based heuristic too
      local fname="$(basename "$f" .gguf)"
      local norm="$(echo "$rel" | sed 's|/|-|g')"
      if [[ "$norm" == *"$fname"* || "$fname" == *"${rel##*/}"* ]]; then
        match="$f"; break
      fi
    fi
  done

  if [[ -z "$match" ]]; then
    echo "NO MATCH for $rel (digest $digest, size $cas_size)" >&2
    return 1
  fi

  echo "Relinking $rel: $cas -> $match"
  if [[ -e "$cas" ]]; then sudo -A -p '' rm "$cas"; fi
  sudo -A -p '' ln -s "$match" "$cas"
}

if [[ $# -ge 1 ]]; then
  case "$1" in
    */*:*) ns="${1%/*}"; rest="${1#*/}"; name="${rest%:*}"; variant="${rest#*:}"; m="${MANIFESTS}/${ns}/${name}/${variant}" ;;
    *:*)   name="${1%:*}"; variant="${1#*:}";                                  m="${MANIFESTS}/library/${name}/${variant}" ;;
    *)     m="${MANIFESTS}/library/${1}/latest" ;;
  esac
  scan_one "$m"
else
  find "$MANIFESTS" -type f | while read -r m; do scan_one "$m" || true; done
fi

echo
echo "Final symlink audit:"
"${LOCAL_LLM_AGENT_ROOT}/scripts/ollama/check-symlinks.sh"
