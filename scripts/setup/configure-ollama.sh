#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

if ! command -v ollama >/dev/null 2>&1; then
  echo "Warning: ollama not found. Install it first:" >&2
  echo "  ./scripts/setup/install-ollama.sh" >&2
  echo "Continuing to write systemd override (valid before install)." >&2
  echo >&2
fi

OVERRIDE_DIR="/etc/systemd/system/ollama.service.d"
OVERRIDE_FILE="${OVERRIDE_DIR}/override.conf"
TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

cat > "$TMP_FILE" <<EOF
[Service]
Environment="OLLAMA_MODELS=${OLLAMA_MODELS}"
Environment="OLLAMA_HOST=127.0.0.1:11434"
Environment="OLLAMA_KEEP_ALIVE=10m"
Environment="OLLAMA_NO_CLOUD=1"
Environment="OLLAMA_NUM_PARALLEL=1"
EOF

echo "Ollama override to install at ${OVERRIDE_FILE}:"
cat "$TMP_FILE"
echo

if [[ "$DRY_RUN" == "1" ]]; then
  echo "Dry run only; not writing systemd override."
  exit 0
fi

mkdir -p "$OLLAMA_MODELS"
sudo mkdir -p "$OVERRIDE_DIR"
sudo install -m 0644 "$TMP_FILE" "$OVERRIDE_FILE"
sudo systemctl daemon-reload

echo "Configured Ollama model store: ${OLLAMA_MODELS}"
echo "Start it with: sudo systemctl start ollama"
