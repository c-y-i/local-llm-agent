#!/usr/bin/env bash
set -euo pipefail

# Start Ollama service if needed, then list local models.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

EXPECTED_MODELS="$OLLAMA_MODELS"

if systemctl is-active --quiet ollama; then
  echo "Ollama service is already running."
else
  echo "Ollama service is not running; starting it now..."
  sudo systemctl start ollama
fi

echo "Ollama status: $(systemctl is-active ollama)"
echo

SERVICE_ENV="$(systemctl show ollama --property=Environment --value || true)"
if [[ "$SERVICE_ENV" != *"OLLAMA_MODELS=${EXPECTED_MODELS}"* ]]; then
  echo "Ollama systemd model path is not set to the current folder."
  echo "Expected: OLLAMA_MODELS=${EXPECTED_MODELS}"
  echo "Current: ${SERVICE_ENV:-<unset>}"
  echo
  cat <<EOF
Fix it with:
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/override.conf >/dev/null <<'SERVICE_OVERRIDE'
[Service]
Environment="OLLAMA_MODELS=${EXPECTED_MODELS}"
Environment="OLLAMA_HOST=127.0.0.1:11434"
Environment="OLLAMA_KEEP_ALIVE=10m"
Environment="OLLAMA_NO_CLOUD=1"
Environment="OLLAMA_NUM_PARALLEL=1"
SERVICE_OVERRIDE
sudo systemctl daemon-reload
sudo systemctl restart ollama
EOF
  exit 1
fi

echo "Local models:"
ollama list

echo
echo "Usage hint: ollama run mistral \"Explain Linux page cache in two sentences.\""
