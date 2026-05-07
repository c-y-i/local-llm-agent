#!/usr/bin/env bash
set -euo pipefail

UNIT_NAME="litellm-proxy.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

UNIT_SRC="${LOCAL_LLM_AGENT_ROOT}/systemd/${UNIT_NAME}.in"
UNIT_DST="/etc/systemd/system/${UNIT_NAME}"
TMP_UNIT="$(mktemp)"
trap 'rm -f "$TMP_UNIT"' EXIT

if [[ ! -f "$UNIT_SRC" ]]; then
  echo "Unit template not found: $UNIT_SRC" >&2
  exit 1
fi

sed \
  -e "s|@LOCAL_LLM_AGENT_ROOT@|${LOCAL_LLM_AGENT_ROOT}|g" \
  -e "s|@SERVICE_USER@|${SERVICE_USER}|g" \
  -e "s|@SERVICE_GROUP@|${SERVICE_GROUP}|g" \
  "$UNIT_SRC" > "$TMP_UNIT"

echo "Generated ${UNIT_NAME}:"
cat "$TMP_UNIT"
echo

if [[ "$DRY_RUN" == "1" ]]; then
  echo "Dry run only; not installing ${UNIT_DST}."
  exit 0
fi

sudo install -m 0644 "$TMP_UNIT" "$UNIT_DST"
sudo systemctl daemon-reload
sudo systemctl disable "$UNIT_NAME" >/dev/null 2>&1 || true

echo "Installed ${UNIT_DST}"
echo
echo "Manual controls:"
echo "  sudo systemctl start litellm-proxy"
echo "  sudo systemctl status litellm-proxy"
echo "  sudo systemctl stop litellm-proxy"
echo "  journalctl -u litellm-proxy -f"
