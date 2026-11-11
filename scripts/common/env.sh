#!/usr/bin/env bash
# Shared path defaults for local-llm-agent.
#
# Source this from scripts instead of hardcoding a machine path. The repository
# contains code and documentation only. Heavy state lives under LLM_ROOT.

if [[ -z "${LOCAL_LLM_AGENT_ROOT+x}" ]]; then
  _env_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  LOCAL_LLM_AGENT_ROOT="$(cd "${_env_dir}/../.." && pwd)"
  unset _env_dir
else
  LOCAL_LLM_AGENT_ROOT="$(cd "$LOCAL_LLM_AGENT_ROOT" && pwd)"
fi

LOCAL_LLM_AGENT_PARENT="$(cd "${LOCAL_LLM_AGENT_ROOT}/.." && pwd)"

if [[ -f "${LOCAL_LLM_AGENT_ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${LOCAL_LLM_AGENT_ROOT}/.env"
  set +a
fi

LLM_ROOT="${LLM_ROOT:-${HOME}/LLM}"
LLAMA_CPP_ROOT="${LLAMA_CPP_ROOT:-${LLM_ROOT}/llama.cpp}"
OLLAMA_ROOT="${OLLAMA_ROOT:-${LLM_ROOT}/ollama}"
LLM_MODELS_DIR="${LLM_MODELS_DIR:-${LLM_ROOT}/models}"
OLLAMA_MODELS="${OLLAMA_MODELS:-${OLLAMA_ROOT}/models/llm}"
HF_HOME="${HF_HOME:-${LLM_ROOT}/huggingface}"
STRATA_HOME="${STRATA_HOME:-${LLM_ROOT}/strata}"
STRATA_MODELS_DIR="${STRATA_MODELS_DIR:-${LLM_ROOT}/models/strata}"
LLM_VENV_DIR="${LLM_VENV_DIR:-${LLM_ROOT}/.venv}"
LLM_RUN_DIR="${LLM_RUN_DIR:-${LLM_ROOT}/run}"
LLM_CODEX_HOME="${LLM_CODEX_HOME:-${LLM_ROOT}/codex-local}"
LLM_HERMES_HOME="${LLM_HERMES_HOME:-${LLM_ROOT}/hermes-local}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
LLAMA_CPP_BIN="${LLAMA_CPP_BIN:-${LLAMA_CPP_ROOT}/build/bin/llama-cli}"
LLAMA_SERVER_BIN="${LLAMA_SERVER_BIN:-${LLAMA_CPP_ROOT}/build/bin/llama-server}"
if [[ -z "${VLLM_BIN+x}" ]]; then
  if [[ -x "${LLM_VENV_DIR}/bin/vllm" ]]; then
    VLLM_BIN="${LLM_VENV_DIR}/bin/vllm"
  else
    VLLM_BIN="vllm"
  fi
fi
if [[ -z "${STRATA_BIN+x}" ]]; then
  if [[ -x "${HOME}/.local/bin/strata" ]]; then
    STRATA_BIN="${HOME}/.local/bin/strata"
  else
    STRATA_BIN="strata"
  fi
fi

LLAMA_CPP_HOST="${LLAMA_CPP_HOST:-127.0.0.1}"
LLAMA_CPP_PORT="${LLAMA_CPP_PORT:-8080}"
VLLM_HOST="${VLLM_HOST:-127.0.0.1}"
VLLM_PORT="${VLLM_PORT:-8000}"
STRATA_HOST="${STRATA_HOST:-127.0.0.1}"
STRATA_PORT="${STRATA_PORT:-8082}"
OLLAMA_PROXY_HOST="${OLLAMA_PROXY_HOST:-127.0.0.1}"
OLLAMA_PROXY_PORT="${OLLAMA_PROXY_PORT:-4000}"

LLAMA_CPP_BASE_URL="${LLAMA_CPP_BASE_URL:-http://${LLAMA_CPP_HOST}:${LLAMA_CPP_PORT}}"
VLLM_BASE_URL="${VLLM_BASE_URL:-http://${VLLM_HOST}:${VLLM_PORT}}"
STRATA_BASE_URL="${STRATA_BASE_URL:-http://${STRATA_HOST}:${STRATA_PORT}}"
OLLAMA_PROXY_BASE_URL="${OLLAMA_PROXY_BASE_URL:-http://${OLLAMA_PROXY_HOST}:${OLLAMA_PROXY_PORT}}"

SERVICE_USER="${SERVICE_USER:-${SUDO_USER:-$(id -un)}}"
SERVICE_GROUP="${SERVICE_GROUP:-$(id -gn "$SERVICE_USER" 2>/dev/null || id -gn)}"

export LOCAL_LLM_AGENT_ROOT LOCAL_LLM_AGENT_PARENT
export LLM_ROOT
export LLAMA_CPP_ROOT OLLAMA_ROOT LLM_MODELS_DIR OLLAMA_MODELS
export HF_HOME STRATA_HOME STRATA_MODELS_DIR LLM_VENV_DIR LLM_RUN_DIR
export LLM_CODEX_HOME LLM_HERMES_HOME
export OLLAMA_BASE_URL
export LLAMA_CPP_BIN LLAMA_SERVER_BIN VLLM_BIN STRATA_BIN
export LLAMA_CPP_HOST LLAMA_CPP_PORT VLLM_HOST VLLM_PORT
export STRATA_HOST STRATA_PORT OLLAMA_PROXY_HOST OLLAMA_PROXY_PORT
export LLAMA_CPP_BASE_URL VLLM_BASE_URL STRATA_BASE_URL OLLAMA_PROXY_BASE_URL
export SERVICE_USER SERVICE_GROUP
