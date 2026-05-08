#!/usr/bin/env bash
set -euo pipefail

# Copy a compatible Ollama binary into the Portable LLM Launcher bin directory.
# This does not install a host service. It only prepares a foreground launcher
# for machines that can run the copied OS/CPU build.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

usage() {
  cat <<EOF
Usage: $0 [--from /path/to/ollama] [--os linux|darwin|windows] [--arch amd64|arm64]

Copies an Ollama executable into:
  ${LOCAL_LLM_AGENT_PARENT}/bin/ollama/<os>-<arch>/ollama[.exe]

If --from is omitted, the script uses the first "ollama" found on PATH.
If --os/--arch are omitted, they are detected from the current machine.
EOF
}

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

src=""
target_os=""
target_arch=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --from)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      src="$2"
      shift 2
      ;;
    --os)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      target_os="$2"
      shift 2
      ;;
    --arch)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      target_arch="$2"
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

if [[ ! -f "$src" ]]; then
  echo "Not a file: ${src}" >&2
  exit 1
fi

target_os="${target_os:-$(detect_os)}"
target_arch="${target_arch:-$(detect_arch)}"

case "$target_os" in
  linux|darwin|windows) ;;
  *)
    echo "Unsupported --os value: ${target_os}" >&2
    exit 2
    ;;
esac

case "$target_arch" in
  amd64|arm64) ;;
  *)
    echo "Unsupported --arch value: ${target_arch}" >&2
    exit 2
    ;;
esac

ext=""
if [[ "$target_os" == "windows" ]]; then
  ext=".exe"
fi

dest_dir="${LOCAL_LLM_AGENT_PARENT}/bin/ollama/${target_os}-${target_arch}"
dest="${dest_dir}/ollama${ext}"

mkdir -p "$dest_dir"
cp "$src" "$dest"
chmod +x "$dest" 2>/dev/null || true

echo "Portable LLM Launcher binary copied:"
echo "  ${dest}"
echo
echo "Start with:"
case "$target_os" in
  windows)
    echo "  ${LOCAL_LLM_AGENT_ROOT}/scripts/ollama/portable-llm-launcher.cmd"
    ;;
  *)
    echo "  ${LOCAL_LLM_AGENT_ROOT}/scripts/ollama/portable-llm-launcher.sh"
    ;;
esac
