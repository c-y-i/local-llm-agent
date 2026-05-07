#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env.sh
source "${SCRIPT_DIR}/env.sh"

# Print core local LLM environment paths.
echo "=== local-llm-agent workspace ==="
echo "Repo root        : ${LOCAL_LLM_AGENT_ROOT}"
echo "Shared GGUFs     : ${LLM_MODELS_DIR}"
echo "Modelfiles (pers): ${LOCAL_LLM_AGENT_ROOT}/modelfiles/personalities"
echo "Modelfiles (gguf): ${LOCAL_LLM_AGENT_ROOT}/modelfiles/gguf"
echo "Scripts (common) : ${LOCAL_LLM_AGENT_ROOT}/scripts/common"
echo "Scripts (ollama) : ${LOCAL_LLM_AGENT_ROOT}/scripts/ollama"
echo "Scripts (llamacp): ${LOCAL_LLM_AGENT_ROOT}/scripts/llama-cpp"
echo "Tuning           : ${LOCAL_LLM_AGENT_ROOT}/tuning"
echo "Docs             : ${LOCAL_LLM_AGENT_ROOT}/docs"
echo
echo "=== llama.cpp ==="
echo "Root             : ${LLAMA_CPP_ROOT}"
echo "Source           : ${LLAMA_CPP_ROOT}/src"
echo "Build            : ${LLAMA_CPP_ROOT}/build"
echo "Binaries         : ${LLAMA_CPP_ROOT}/build/bin"
echo
echo "=== Ollama ==="
echo "Service unit     : /etc/systemd/system/ollama.service.d/override.conf"
echo "OLLAMA_ROOT      : ${OLLAMA_ROOT}"
echo "OLLAMA_MODELS    : ${OLLAMA_MODELS}"
echo "API              : http://127.0.0.1:11434"
