#!/usr/bin/env bash
set -euo pipefail

# Start a foreground Ollama server from this portable layout.
# Prefer a bundled SSD binary, then OLLAMA_BIN, then a host-installed ollama.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

os="$(uname -s | tr '[:upper:]' '[:lower:]')"
arch="$(uname -m)"
case "$arch" in
  x86_64|amd64) arch="amd64" ;;
  aarch64|arm64) arch="arm64" ;;
esac

bundled="${LOCAL_LLM_AGENT_PARENT}/bin/ollama/${os}-${arch}/ollama"

if [[ -n "${OLLAMA_BIN:-}" ]]; then
  ollama_bin="$OLLAMA_BIN"
elif [[ -x "$bundled" ]]; then
  ollama_bin="$bundled"
elif command -v ollama >/dev/null 2>&1; then
  ollama_bin="$(command -v ollama)"
else
  cat >&2 <<EOF
No compatible Ollama binary found.

Expected bundled binary:
  ${bundled}

Options:
  1. Install Ollama on this host and rerun this script.
  2. On a matching machine, run:
     ${LOCAL_LLM_AGENT_ROOT}/scripts/ollama/install-portable-ollama.sh
  3. Set OLLAMA_BIN=/path/to/ollama.
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
  OLLAMA_HOST=127.0.0.1:11435 $0
EOF
    exit 1
  fi
fi

echo "Portable Ollama server"
echo "  binary        : ${ollama_bin}"
echo "  OLLAMA_MODELS : ${OLLAMA_MODELS}"
echo "  OLLAMA_HOST   : ${OLLAMA_HOST}"
echo
echo "In another terminal:"
echo "  OLLAMA_HOST=${OLLAMA_HOST} ${ollama_bin} list"
echo "  OLLAMA_HOST=${OLLAMA_HOST} ${ollama_bin} run qwen3:4b"
echo

exec "$ollama_bin" serve
