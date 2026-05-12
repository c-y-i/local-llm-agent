#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

if command -v ollama >/dev/null 2>&1; then
  echo "Ollama already installed: $(command -v ollama)"
  ollama --version 2>/dev/null || true
  exit 0
fi

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64)  ;;
  aarch64) ;;
  *) echo "Unsupported architecture: $ARCH" >&2; exit 1 ;;
esac

echo "Detected: $ARCH"
echo "Will run: curl -fsSL https://ollama.com/install.sh | sh"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "Dry run only; not installing."
  exit 0
fi

curl -fsSL https://ollama.com/install.sh | sh

echo
echo "Ollama installed. Configure and start:"
echo "  ./scripts/setup/configure-ollama.sh"
echo "  sudo systemctl start ollama"
