#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

REQUIRED_MISSING=0

check_cmd() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    printf 'ok   %-18s %s\n' "$name" "$(command -v "$name")"
  else
    printf 'miss %-18s not found\n' "$name"
    REQUIRED_MISSING=$((REQUIRED_MISSING + 1))
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
echo "  LLM_ROOT=${LLM_ROOT}"
echo "  LLAMA_CPP_ROOT=${LLAMA_CPP_ROOT}"
echo "  OLLAMA_ROOT=${OLLAMA_ROOT}"
echo "  OLLAMA_MODELS=${OLLAMA_MODELS}"
echo "  LLM_MODELS_DIR=${LLM_MODELS_DIR}"
echo "  HF_HOME=${HF_HOME}"
echo "  STRATA_HOME=${STRATA_HOME}"
echo "  STRATA_MODELS_DIR=${STRATA_MODELS_DIR}"
echo "  LLM_VENV_DIR=${LLM_VENV_DIR}"
echo "  LLAMA_CPP_BASE_URL=${LLAMA_CPP_BASE_URL}"
echo "  VLLM_BASE_URL=${VLLM_BASE_URL}"
echo "  STRATA_BASE_URL=${STRATA_BASE_URL}"
echo

echo "commands"
for cmd in git cmake make cc c++ curl python3; do
  check_cmd "$cmd"
done
check_cmd_optional ollama
check_cmd_optional systemctl
check_cmd_optional nvcc
check_cmd_optional nvidia-smi
check_cmd_optional codex
check_cmd_optional claude
check_cmd_optional hermes
check_cmd_optional vllm
check_cmd_optional strata
echo

if command -v nvidia-smi >/dev/null 2>&1; then
  echo "gpu"
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null || true
fi

echo
echo "directories"
for dir in "$LOCAL_LLM_AGENT_ROOT" "$LLM_ROOT" "$LLAMA_CPP_ROOT" "$OLLAMA_ROOT" "$LLM_MODELS_DIR" "$OLLAMA_MODELS" "$HF_HOME" "$STRATA_HOME" "$STRATA_MODELS_DIR" "$LLM_VENV_DIR"; do
  if [[ -d "$dir" ]]; then
    echo "ok   $dir"
  else
    echo "miss $dir"
  fi
done

if (( REQUIRED_MISSING > 0 )); then
  echo
  echo "${REQUIRED_MISSING} required command(s) are missing." >&2
  exit 1
fi
