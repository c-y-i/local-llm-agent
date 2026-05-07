#!/usr/bin/env bash
set -euo pipefail

# Audit Ollama's CAS for symlinks pointing into the shared model directory.
# Reports: count, total target size, dangling links, and a per-model summary.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

CAS="${OLLAMA_MODELS}/blobs"
LLM_MODELS="$LLM_MODELS_DIR"

if [[ ! -d "$CAS" ]]; then
  echo "Ollama CAS not found: $CAS" >&2
  exit 1
fi

ok=0
dangling=0
total_size=0

declare -A by_target

for link in "$CAS"/sha256-*; do
  [[ -L "$link" ]] || continue
  target="$(readlink -f "$link" 2>/dev/null || true)"
  src_target="$(readlink "$link")"
  case "$src_target" in
    "$LLM_MODELS"/*) ;;
    *) continue ;;
  esac
  if [[ -f "$target" ]]; then
    ok=$((ok + 1))
    sz=$(stat -c '%s' "$target" 2>/dev/null || echo 0)
    total_size=$((total_size + sz))
    name="$(basename "$src_target")"
    by_target["$name"]=$((${by_target["$name"]:-0} + 1))
  else
    dangling=$((dangling + 1))
    echo "DANGLING: $link -> $src_target" >&2
  fi
done

echo "Symlinks pointing into ${LLM_MODELS}:"
for name in "${!by_target[@]}"; do
  printf '  %-40s  refs=%d\n' "$name" "${by_target[$name]}"
done | sort
echo
printf 'Healthy : %d\n' "$ok"
printf 'Dangling: %d\n' "$dangling"
printf 'Total size: %.2f GB\n' "$(echo "$total_size / 1000000000" | bc -l)"

if [[ "$dangling" -gt 0 ]]; then
  exit 2
fi
