#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

check_cmd() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    printf 'ok   %-18s %s\n' "$name" "$(command -v "$name")"
  else
    printf 'miss %-18s not found\n' "$name"
  fi
}

check_cmd_optional() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    printf 'ok   %-18s %s\n' "$name" "$(command -v "$name")"
  else
    printf 'opt  %-18s not found (optional)\n' "$name"
  fi
}

echo "local-llm-agent paths"
echo "  LOCAL_LLM_AGENT_ROOT=${LOCAL_LLM_AGENT_ROOT}"
echo "  LLAMA_CPP_ROOT=${LLAMA_CPP_ROOT}"
echo "  OLLAMA_ROOT=${OLLAMA_ROOT}"
echo "  OLLAMA_MODELS=${OLLAMA_MODELS}"
echo "  LLM_MODELS_DIR=${LLM_MODELS_DIR}"
echo

echo "commands"
for cmd in git cmake make cc c++ curl python3; do
  check_cmd "$cmd"
done
check_cmd ollama
check_cmd systemctl
check_cmd_optional nvidia-smi
echo

if command -v nvidia-smi >/dev/null 2>&1; then
  echo "gpu"
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null || true
fi

echo
echo "directories"
for dir in "$LOCAL_LLM_AGENT_ROOT" "$LLAMA_CPP_ROOT" "$OLLAMA_ROOT" "$LLM_MODELS_DIR" "$OLLAMA_MODELS"; do
  if [[ -d "$dir" ]]; then
    echo "ok   $dir"
  else
    echo "miss $dir"
  fi
done
