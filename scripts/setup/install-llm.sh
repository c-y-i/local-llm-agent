#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

BIN_DIR="${HOME}/.local/bin"
TARGET="${BIN_DIR}/llm"

mkdir -p "$BIN_DIR"
ln -sfn "${LOCAL_LLM_AGENT_ROOT}/llm" "$TARGET"

echo "Installed ${TARGET} -> ${LOCAL_LLM_AGENT_ROOT}/llm"
if [[ ":${PATH}:" != *":${BIN_DIR}:"* ]]; then
  echo "Add ${BIN_DIR} to PATH, then open a new terminal:"
  echo "  export PATH=\"${BIN_DIR}:\$PATH\""
fi
