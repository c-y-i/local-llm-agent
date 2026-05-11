#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

detect_os() {
  case "$(uname -s)" in
    Linux*) echo "linux" ;;
    Darwin*) echo "darwin" ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
    *) uname -s | tr '[:upper:]' '[:lower:]' ;;
  esac
}

detect_arch() {
  case "$(uname -m)" in
    x86_64|amd64) echo "amd64" ;;
    aarch64|arm64) echo "arm64" ;;
    *) uname -m ;;
  esac
}

usage() {
  cat <<EOF
Usage: llm-ollama <ollama-command> [args...]

Runs the Ollama CLI against the portable LLM server.

Examples:
  llm-ollama list
  llm-ollama run qwen3:4b
  llm-ollama ps

Defaults:
  OLLAMA_HOST=${OLLAMA_HOST:-127.0.0.1:14514}
  OLLAMA_MODELS=${OLLAMA_MODELS}
EOF
}

if [[ $# -eq 0 || "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

os="$(detect_os)"
arch="$(detect_arch)"
ext=""
if [[ "$os" == "windows" ]]; then
  ext=".exe"
fi

bundled="${LOCAL_LLM_AGENT_PARENT}/bin/ollama/${os}-${arch}/ollama${ext}"

if [[ -n "${OLLAMA_BIN:-}" ]]; then
  ollama_bin="$OLLAMA_BIN"
elif [[ -x "$bundled" ]]; then
  ollama_bin="$bundled"
elif command -v ollama >/dev/null 2>&1; then
  ollama_bin="$(command -v ollama)"
else
  cat >&2 <<EOF
No compatible Ollama CLI found.

Expected bundled binary:
  ${bundled}

Options:
  1. Install Ollama on this host.
  2. Run ${LOCAL_LLM_AGENT_ROOT}/scripts/ollama/install-portable-llm-binary.sh on a matching host.
  3. Set OLLAMA_BIN=/path/to/ollama.
EOF
  exit 1
fi

export OLLAMA_MODELS
export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:14514}"
export OLLAMA_NO_CLOUD="${OLLAMA_NO_CLOUD:-1}"

exec "$ollama_bin" "$@"
