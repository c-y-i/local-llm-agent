#!/usr/bin/env bash
set -euo pipefail

# Start llama-server with settings suited to Claude Code's tool loop.
#
# Usage:
#   claude-server.sh [model-name] [port]
#   ./scripts/claude/claude-local.sh --backend llama-cpp --model <model-name>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

if [[ $# -lt 1 ]]; then
  set -- "$(find "$LLM_MODELS_DIR" -maxdepth 1 -type f -name '*.gguf' -printf '%f\n' 2>/dev/null |
    sed 's/\.gguf$//' | sort | head -n 1)" "${LLAMA_CPP_PORT}"
elif [[ $# -eq 1 ]]; then
  set -- "$1" "${LLAMA_CPP_PORT}"
fi

export JINJA="${JINJA:-1}"
export N_PARALLEL="${N_PARALLEL:-1}"
exec "${SCRIPT_DIR}/cline-server.sh" "$1" "$2"
