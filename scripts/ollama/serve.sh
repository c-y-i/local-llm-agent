#!/usr/bin/env bash
set -euo pipefail

# Start a foreground Ollama server with this repo's portable model store.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

export OLLAMA_MODELS
export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-10m}"
export OLLAMA_NO_CLOUD="${OLLAMA_NO_CLOUD:-1}"
export OLLAMA_NUM_PARALLEL="${OLLAMA_NUM_PARALLEL:-1}"

echo "Ollama manual server"
echo "  OLLAMA_MODELS=${OLLAMA_MODELS}"
echo "  OLLAMA_HOST=${OLLAMA_HOST}"
echo

host_port="${OLLAMA_HOST#http://}"
host_port="${host_port#https://}"
port="${host_port##*:}"
if command -v ss >/dev/null 2>&1; then
  listener="$(ss -H -tlnp 2>/dev/null | awk -v p=":${port}" '$4 ~ p "$" {print; exit}')"
  if [[ -n "$listener" ]]; then
    echo "Port ${port} is already in use:"
    echo "  $listener"
    echo
    echo "Stop the existing Ollama server first, for example:"
    echo "  pkill -f '^ollama serve$'"
    echo "  sudo systemctl stop ollama"
    exit 1
  fi
fi

echo "In another terminal:"
echo "  ollama list"
echo "  ollama run qwen3:1.7b"
echo

exec ollama serve
