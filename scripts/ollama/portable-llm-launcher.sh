#!/usr/bin/env bash
set -euo pipefail

# Start a foreground Ollama server with this repo's portable model store.
# Use OLLAMA_BIN when set, otherwise use the host-installed ollama.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

if [[ -n "${OLLAMA_BIN:-}" ]]; then
  ollama_bin="$OLLAMA_BIN"
elif command -v ollama >/dev/null 2>&1; then
  ollama_bin="$(command -v ollama)"
else
  cat >&2 <<EOF
No Ollama executable found.

Options:
  1. Install Ollama on this host and rerun this launcher.
  2. Set OLLAMA_BIN=/path/to/ollama.
EOF
  exit 1
fi

export OLLAMA_MODELS
export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-10m}"
export OLLAMA_NO_CLOUD="${OLLAMA_NO_CLOUD:-1}"
export OLLAMA_NUM_PARALLEL="${OLLAMA_NUM_PARALLEL:-1}"

host_port="${OLLAMA_HOST#http://}"
host_port="${host_port#https://}"
port="${host_port##*:}"

if command -v ss >/dev/null 2>&1; then
  listener="$(ss -H -tlnp 2>/dev/null | awk -v p=":${port}" '$4 ~ p "$" {print; exit}')"
  if [[ -n "$listener" ]]; then
    cat >&2 <<EOF
Port ${port} is already in use:
  ${listener}

Use a different port, for example:
  OLLAMA_HOST=127.0.0.1:14514 $0

Use a matching OLLAMA_HOST in both terminals.
EOF
    exit 1
  fi
fi

echo "Portable LLM Launcher"
echo "  binary        : ${ollama_bin}"
echo "  OLLAMA_MODELS : ${OLLAMA_MODELS}"
echo "  OLLAMA_HOST   : ${OLLAMA_HOST}"
echo
echo "In another terminal:"
echo "  OLLAMA_HOST=${OLLAMA_HOST} ${ollama_bin} list"
echo "  OLLAMA_HOST=${OLLAMA_HOST} ${ollama_bin} run qwen3:4b"
echo

exec "$ollama_bin" serve
