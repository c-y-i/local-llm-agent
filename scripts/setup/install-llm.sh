#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

BIN_DIR="${HOME}/.local/bin"
TARGET="${BIN_DIR}/llm"
VENV="${LLM_VENV_DIR}"

mkdir -p "$BIN_DIR"
if [[ ! -f "${VENV}/bin/activate" ]]; then
  echo "Creating managed virtualenv: ${VENV}"
  if ! python3 -m venv "$VENV"; then
    echo "Python venv bootstrap lacks ensurepip; creating the environment without pip."
    echo "Install python3.12-venv later to add pip and vLLM."
    python3 -m venv --clear --without-pip "$VENV"
  fi
fi
if "${VENV}/bin/python" -m pip --version >/dev/null 2>&1; then
  "${VENV}/bin/python" -m pip install --upgrade pip
else
  echo "pip is not available in ${VENV}."
  echo "Install it with: sudo apt install python3.12-venv"
fi
if [[ -e "${LOCAL_LLM_AGENT_ROOT}/.venv" && ! -L "${LOCAL_LLM_AGENT_ROOT}/.venv" ]]; then
  echo "Warning: ${LOCAL_LLM_AGENT_ROOT}/.venv exists and is not a symlink; leaving it unchanged."
else
  ln -sfn "$VENV" "${LOCAL_LLM_AGENT_ROOT}/.venv"
fi
ln -sfn "${LOCAL_LLM_AGENT_ROOT}/llm" "$TARGET"
"${LOCAL_LLM_AGENT_ROOT}/scripts/setup/install-agent-commands.sh"

echo "Installed ${TARGET} -> ${LOCAL_LLM_AGENT_ROOT}/llm"
echo "Activate the environment in each new shell:"
echo "  source ${LOCAL_LLM_AGENT_ROOT}/.venv/bin/activate"
if [[ ":${PATH}:" != *":${BIN_DIR}:"* ]]; then
  echo "Add ${BIN_DIR} to PATH, then open a new terminal:"
  echo "  export PATH=\"${BIN_DIR}:\$PATH\""
fi
