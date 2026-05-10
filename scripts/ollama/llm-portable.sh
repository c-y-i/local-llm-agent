#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:14514}"

exec "${SCRIPT_DIR}/portable-llm-launcher.sh" "$@"
