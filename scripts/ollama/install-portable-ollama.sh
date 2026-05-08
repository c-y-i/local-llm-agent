#!/usr/bin/env bash
set -euo pipefail

# Copy a compatible Ollama binary into the portable parent directory.
# This does not install a system service. It only prepares a foreground
# launcher for machines that can run this OS/CPU build.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

usage() {
  cat <<EOF
Usage: $0 [--from /path/to/ollama]

Copies an Ollama executable into:
  ${LOCAL_LLM_AGENT_PARENT}/bin/ollama/<os>-<arch>/ollama

If --from is omitted, the script uses the first "ollama" found on PATH.
EOF
}

src=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --from)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      src="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$src" ]]; then
  if ! src="$(command -v ollama 2>/dev/null)"; then
    echo "ollama is not on PATH. Install Ollama on this host first, or pass --from /path/to/ollama." >&2
    exit 1
  fi
fi

if [[ ! -x "$src" ]]; then
  echo "Not executable: ${src}" >&2
  exit 1
fi

os="$(uname -s | tr '[:upper:]' '[:lower:]')"
arch="$(uname -m)"
case "$arch" in
  x86_64|amd64) arch="amd64" ;;
  aarch64|arm64) arch="arm64" ;;
esac

dest_dir="${LOCAL_LLM_AGENT_PARENT}/bin/ollama/${os}-${arch}"
dest="${dest_dir}/ollama"

mkdir -p "$dest_dir"
cp "$src" "$dest"
chmod +x "$dest"

echo "Portable Ollama binary copied:"
echo "  ${dest}"
echo
echo "Start the SSD-backed server with:"
echo "  ${LOCAL_LLM_AGENT_ROOT}/scripts/ollama/portable-serve.sh"
