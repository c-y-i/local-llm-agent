#!/usr/bin/env bash
set -euo pipefail

# Create local variants from persistent Modelfiles.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

# Edit files under $MODELFILES_DIR and rerun this script.
#
# Format: "target_model|base_model"
MODEL_SPECS=(
  "mistral-local|mistral"
  "phi3-local|phi3"
  "mythomax-local|mythomax"
  "dolphin-local|dolphin-llama3:8b"
)
MODELFILES_DIR="${MODELFILES_DIR:-${LOCAL_LLM_AGENT_ROOT}/modelfiles/personalities}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "ollama not found in PATH."
  exit 1
fi

if ! curl -fsS http://127.0.0.1:11434/api/tags >/dev/null; then
  echo "Ollama API is not reachable at 127.0.0.1:11434"
  echo "Run ${LOCAL_LLM_AGENT_ROOT}/scripts/ollama/serve.sh first."
  exit 1
fi

mkdir -p "$MODELFILES_DIR"

create_placeholder_modelfile() {
  local target="$1"
  local base="$2"
  local modelfile="${MODELFILES_DIR}/${target}.Modelfile"

  if [[ -f "$modelfile" ]]; then
    return
  fi

  cat > "$modelfile" <<EOF
# Output model: ${target}
# Edit SYSTEM/PARAMETER lines below, then rerun:
#   ${LOCAL_LLM_AGENT_ROOT}/scripts/ollama/create_local_models.sh

FROM ${base}
SYSTEM You are a helpful local assistant. [EDIT THIS PROMPT]
PARAMETER temperature 0.7
PARAMETER top_p 0.9
EOF

  echo "Created placeholder Modelfile: $modelfile"
}

for spec in "${MODEL_SPECS[@]}"; do
  IFS='|' read -r target base <<< "$spec"

  if ! ollama show "$base" >/dev/null 2>&1; then
    echo "Skipping ${target}: base model '${base}' not found."
    continue
  fi

  create_placeholder_modelfile "$target" "$base"
  modelfile="${MODELFILES_DIR}/${target}.Modelfile"

  if ! rg -q '^FROM[[:space:]]+' "$modelfile"; then
    echo "Skipping ${target}: missing FROM line in $modelfile"
    continue
  fi

  echo "Creating ${target} from ${modelfile}..."
  ollama create "$target" -f "$modelfile" >/dev/null
done

echo
echo "Local variants ready (if base models were present):"
ollama list | awk 'NR==1 || /-local/'
echo
echo "Modelfiles directory: ${MODELFILES_DIR}"
echo "Edit those files and rerun this script to apply changes."
echo
echo "Try:"
echo "  ollama run mistral-local"
echo "  ollama run phi3-local"
echo "  ollama run mythomax-local"
echo "  ollama run dolphin-local"
