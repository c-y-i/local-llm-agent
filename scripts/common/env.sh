#!/usr/bin/env bash
# Shared path defaults for local-llm-agent.
#
# Source this from scripts instead of hardcoding a machine path. The default
# layout is:
#   <parent>/local-llm-agent   # this repo
#   <parent>/llama-cpp         # llama.cpp source/build
#   <parent>/Ollama            # Ollama model store

if [[ -z "${LOCAL_LLM_AGENT_ROOT+x}" ]]; then
  _env_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  LOCAL_LLM_AGENT_ROOT="$(cd "${_env_dir}/../.." && pwd)"
  unset _env_dir
else
  LOCAL_LLM_AGENT_ROOT="$(cd "$LOCAL_LLM_AGENT_ROOT" && pwd)"
fi

LOCAL_LLM_AGENT_PARENT="$(cd "${LOCAL_LLM_AGENT_ROOT}/.." && pwd)"

LLAMA_CPP_ROOT="${LLAMA_CPP_ROOT:-${LOCAL_LLM_AGENT_PARENT}/llama-cpp}"
OLLAMA_ROOT="${OLLAMA_ROOT:-${LOCAL_LLM_AGENT_PARENT}/Ollama}"
LLM_MODELS_DIR="${LLM_MODELS_DIR:-${LOCAL_LLM_AGENT_ROOT}/models}"
OLLAMA_MODELS="${OLLAMA_MODELS:-${OLLAMA_ROOT}/models/llm}"
LLAMA_CPP_BIN="${LLAMA_CPP_BIN:-${LLAMA_CPP_ROOT}/build/bin/llama-cli}"
LLAMA_SERVER_BIN="${LLAMA_SERVER_BIN:-${LLAMA_CPP_ROOT}/build/bin/llama-server}"
SERVICE_USER="${SERVICE_USER:-${SUDO_USER:-$(id -un)}}"
SERVICE_GROUP="${SERVICE_GROUP:-$(id -gn "$SERVICE_USER" 2>/dev/null || id -gn)}"

export LOCAL_LLM_AGENT_ROOT LOCAL_LLM_AGENT_PARENT
export LLAMA_CPP_ROOT OLLAMA_ROOT LLM_MODELS_DIR OLLAMA_MODELS
export LLAMA_CPP_BIN LLAMA_SERVER_BIN SERVICE_USER SERVICE_GROUP
