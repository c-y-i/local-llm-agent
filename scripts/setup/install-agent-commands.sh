#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

BIN_DIR="${HOME}/.local/bin"
LAUNCHER="${LOCAL_LLM_AGENT_ROOT}/scripts/agents/launch-local.sh"

mkdir -p "$BIN_DIR"
for agent in claude codex hermes; do
  ln -sfn "$LAUNCHER" "${BIN_DIR}/${agent}-local"
done

echo "Installed local agent commands:"
echo "  ${BIN_DIR}/claude-local"
echo "  ${BIN_DIR}/codex-local"
echo "  ${BIN_DIR}/hermes-local"
