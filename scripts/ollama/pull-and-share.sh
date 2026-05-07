#!/usr/bin/env bash
set -euo pipefail

# Pull a model from the Ollama registry, then move its GGUF blob out of CAS
# into the shared model directory and replace the CAS path with
# a symlink. Result: the model is usable by both Ollama and llama.cpp,
# with a single physical copy stored in $LLM_MODELS_DIR.
#
# Usage:
#   pull-and-share.sh <ollama-tag> [friendly-name]
#   pull-and-share.sh qwen3:8b
#   pull-and-share.sh wangtcalex/foo:latest custom-foo
#
# If [friendly-name] is omitted, it's derived from the tag:
#   "qwen3:4b"            → "qwen3-4b.gguf"
#   "phi4-mini:latest"    → "phi4-mini.gguf"
#   "wangtcalex/foo:bar"  → "wangtcalex-foo-bar.gguf"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

CAS="${OLLAMA_MODELS}/blobs"
MANIFESTS="${OLLAMA_MODELS}/manifests/registry.ollama.ai"
LLM_MODELS="$LLM_MODELS_DIR"
ASKPASS="${SUDO_ASKPASS:-}"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <ollama-tag> [friendly-name]" >&2
  exit 1
fi

tag="$1"
friendly="${2:-}"

# Derive friendly name if not given
if [[ -z "$friendly" ]]; then
  derived="$(echo "$tag" | sed 's|/|-|g; s|:|-|g')"
  derived="${derived%-latest}"
  friendly="${derived}.gguf"
fi
case "$friendly" in
  *.gguf) ;;
  *) friendly="${friendly}.gguf" ;;
esac

dst="${LLM_MODELS}/${friendly}"

if [[ -e "$dst" ]]; then
  echo "Destination already exists: $dst" >&2
  exit 1
fi

echo "==> ollama pull $tag"
ollama pull "$tag"

# Resolve manifest path: tag may be "ns/name:variant" or "name:variant"
case "$tag" in
  */*:*)
    ns="${tag%/*}"; rest="${tag#*/}"; name="${rest%:*}"; variant="${rest#*:}"
    manifest="${MANIFESTS}/${ns}/${name}/${variant}"
    ;;
  *:*)
    name="${tag%:*}"; variant="${tag#*:}"
    manifest="${MANIFESTS}/library/${name}/${variant}"
    ;;
  *)
    manifest="${MANIFESTS}/library/${tag}/latest"
    ;;
esac

if [[ ! -f "$manifest" ]]; then
  echo "Manifest not found after pull: $manifest" >&2
  exit 1
fi

digest="$(python3 -c '
import json, sys
m = json.load(open(sys.argv[1]))
for layer in m["layers"]:
    if layer["mediaType"] == "application/vnd.ollama.image.model":
        print(layer["digest"].replace(":", "-"))
        sys.exit(0)
sys.exit("no GGUF layer")
' "$manifest")"

src="${CAS}/${digest}"
if [[ ! -f "$src" || -L "$src" ]]; then
  echo "Source blob not found or already a symlink: $src" >&2
  exit 1
fi

echo "==> Moving blob to ${dst} and symlinking back"
sudo -A -p '' mv "$src" "$dst"
sudo -A -p '' ln -s "$dst" "$src"
sudo -A -p '' chown "${SERVICE_USER}:ollama" "$dst"
sudo -A -p '' chmod 644 "$dst"

echo "==> Verifying"
ls -la "$src"
ls -la "$dst"
echo "Done. Available as both:"
echo "  ollama run ${tag}"
echo "  ${LLAMA_CPP_BIN} -m ${dst}"
