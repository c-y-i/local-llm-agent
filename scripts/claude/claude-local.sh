#!/usr/bin/env bash
set -euo pipefail

# Launch Claude Code against a local Anthropic-compatible backend.
#
# llama.cpp, vLLM, and Strata implement Anthropic's Messages API directly.
# Ollama still uses the compatibility proxy in scripts/ollama/.
#
# Usage:
#   claude-local.sh [--backend llama-cpp|vllm|strata|ollama]
#                   [--model MODEL] [--check] [claude args...]
#
# If --backend is omitted, the first reachable backend is selected in this
# order: llama.cpp, vLLM, Strata, Ollama proxy.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

CLAUDE_BIN="${CLAUDE_BIN:-claude}"
backend="${LLM_BACKEND:-}"
model="${ANTHROPIC_MODEL:-}"
check_only=0
claude_args=()

usage() {
  cat <<EOF
Usage: $0 [--backend llama-cpp|vllm|strata|ollama] [--model MODEL] [--check] [claude args...]

Environment:
  LLM_BACKEND                 Default backend when --backend is omitted
  ANTHROPIC_MODEL             Default model when --model is omitted
  LLAMA_CPP_BASE_URL          Default: ${LLAMA_CPP_BASE_URL}
  VLLM_BASE_URL               Default: ${VLLM_BASE_URL}
  STRATA_BASE_URL             Default: ${STRATA_BASE_URL}
  OLLAMA_PROXY_BASE_URL       Default: ${OLLAMA_PROXY_BASE_URL}
  LLAMA_CPP_API_KEY           Optional key for llama-server --api-key
  LLAMA_SERVER_API_KEY        Alternate name used by llama.cpp start scripts
  VLLM_API_KEY                Optional key when vLLM authentication is enabled
  STRATA_API_KEY              API key configured when launching Strata
  OLLAMA_PROXY_API_KEY        Default: local

Use --check to validate the backend and print the Claude Code environment
without starting Claude Code.
EOF
}

die() {
  echo "error: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backend)
      [[ $# -ge 2 ]] || die "--backend requires a value"
      backend="$2"
      shift 2
      ;;
    --backend=*)
      backend="${1#*=}"
      shift
      ;;
    --model)
      [[ $# -ge 2 ]] || die "--model requires a value"
      model="$2"
      shift 2
      ;;
    --model=*)
      model="${1#*=}"
      shift
      ;;
    --check)
      check_only=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      claude_args+=("$@")
      break
      ;;
    *)
      claude_args+=("$1")
      shift
      ;;
  esac
done

backend_url() {
  case "$1" in
    llama-cpp) printf '%s' "${LLAMA_CPP_BASE_URL%/}" ;;
    vllm) printf '%s' "${VLLM_BASE_URL%/}" ;;
    strata) printf '%s' "${STRATA_BASE_URL%/}" ;;
    ollama) printf '%s' "${OLLAMA_PROXY_BASE_URL%/}" ;;
    *) return 1 ;;
  esac
}

backend_token() {
  case "$1" in
    llama-cpp) printf '%s' "${LLAMA_CPP_API_KEY:-${LLAMA_SERVER_API_KEY:-local}}" ;;
    vllm) printf '%s' "${VLLM_API_KEY:-local}" ;;
    strata) printf '%s' "${STRATA_API_KEY:-local}" ;;
    ollama) printf '%s' "${OLLAMA_PROXY_API_KEY:-local}" ;;
    *) return 1 ;;
  esac
}

backend_reachable() {
  local name="$1"
  local url
  url="$(backend_url "$name")" || return 1
  if [[ "$name" == "ollama" ]]; then
    curl -fsS --max-time 2 "${url}/health" >/dev/null 2>&1
  else
    curl -fsS --max-time 2 "${url}/v1/models" >/dev/null 2>&1
  fi
}

backend_models() {
  local url
  url="$(backend_url "$1")" || return 1
  curl -fsS --max-time 3 "${url}/v1/models" 2>/dev/null |
    python3 -c 'import json,sys; data=json.load(sys.stdin); [print(x.get("id", "")) for x in data.get("data", []) if x.get("id")]'
}

if [[ -z "$backend" ]]; then
  for candidate in llama-cpp vllm strata ollama; do
    if backend_reachable "$candidate"; then
      backend="$candidate"
      break
    fi
  done
fi

[[ -n "$backend" ]] || die "no local backend is reachable; start llama.cpp, vLLM, Strata, or the Ollama proxy first"

case "$backend" in
  llama-cpp|vllm|strata|ollama) ;;
  *) die "unsupported backend '$backend' (expected llama-cpp, vllm, strata, or ollama)" ;;
esac

base_url="$(backend_url "$backend")"
[[ -n "$base_url" ]] || die "base URL is empty for backend '$backend'"
backend_reachable "$backend" || die "$backend is not reachable at $base_url"

if [[ -z "$model" && "$backend" != "ollama" ]]; then
  mapfile -t available_models < <(backend_models "$backend" || true)
  if [[ ${#available_models[@]} -eq 1 ]]; then
    model="${available_models[0]}"
  elif [[ ${#available_models[@]} -gt 1 ]]; then
    printf 'Available models for %s:\n' "$backend" >&2
    printf '  %s\n' "${available_models[@]}" >&2
    die "multiple models are available; select one with --model"
  fi
fi

[[ -n "$model" ]] || die "model is required for the Ollama proxy; pass --model"

token="$(backend_token "$backend")"
export ANTHROPIC_BASE_URL="$base_url"
export ANTHROPIC_AUTH_TOKEN="$token"
export ANTHROPIC_API_KEY="$token"
export ANTHROPIC_MODEL="$model"
export ANTHROPIC_DEFAULT_OPUS_MODEL="$model"
export ANTHROPIC_DEFAULT_SONNET_MODEL="$model"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$model"
export ANTHROPIC_DEFAULT_FABLE_MODEL="$model"
export ANTHROPIC_SMALL_FAST_MODEL="$model"
export ANTHROPIC_CUSTOM_MODEL_OPTION="$model"
export ANTHROPIC_CUSTOM_MODEL_OPTION_NAME="${model} (local ${backend})"
export ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION="Local model served by ${backend} at ${base_url}"
export CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY="${CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY:-1}"
# A conservative default prevents Claude Code from assuming a 200K window on
# an unrecognized local model ID. Override it to match the server's N_CTX.
export CLAUDE_CODE_MAX_CONTEXT_TOKENS="${CLAUDE_CODE_MAX_CONTEXT_TOKENS:-32768}"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="${CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC:-1}"
# Newer Claude Code versions add a per-request attribution stamp that can
# defeat local prefix caching.
export CLAUDE_CODE_ATTRIBUTION_HEADER="${CLAUDE_CODE_ATTRIBUTION_HEADER:-0}"

echo "Claude Code local backend:" >&2
echo "  Backend : $backend" >&2
echo "  URL     : $ANTHROPIC_BASE_URL" >&2
echo "  Model   : $ANTHROPIC_MODEL" >&2
echo "  Context : $CLAUDE_CODE_MAX_CONTEXT_TOKENS tokens" >&2

if [[ "$check_only" == "1" ]]; then
  exit 0
fi

command -v "$CLAUDE_BIN" >/dev/null 2>&1 ||
  die "Claude Code CLI '$CLAUDE_BIN' is not installed; see https://code.claude.com/docs/en/setup"

exec "$CLAUDE_BIN" --model "$ANTHROPIC_MODEL" "${claude_args[@]}"
