#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

ROOT_DIR="$OLLAMA_ROOT"
MODEL_DIR="${OLLAMA_MODELS:-${ROOT_DIR}/models/llm}"
HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
SERVICE_HOST="127.0.0.1:11434"
TEMP_HOST="127.0.0.1:11435"
OLLAMA_BIN="${OLLAMA_BIN:-ollama}"

# Conservative starter set for hardware ranging from SBC/CPU systems to small
# GPUs. Larger machines can pull bigger tags manually or from docs/models.md.
MODELS=(
  "qwen3:4b"
  "llama3.2:3b"
  "qwen2.5-coder:3b"
  "phi4-mini"
  "qwen3:1.7b"
  "deepseek-r1:1.5b"
)

die() {
  echo "ERROR: $*" >&2
  exit 1
}

has_model() {
  local model="$1"
  local canonical="$model"
  [[ "$model" != *:* ]] && canonical="${model}:latest"

  OLLAMA_HOST="$HOST" "$OLLAMA_BIN" list 2>/dev/null \
    | awk 'NR > 1 {print $1}' \
    | grep -Fxq -e "$model" -e "$canonical"
}

install_ollama_if_missing() {
  if command -v "$OLLAMA_BIN" >/dev/null 2>&1; then
    echo "Ollama already installed: $("$OLLAMA_BIN" --version)"
    return
  fi

  echo "Ollama is missing; installing with the official install script..."
  curl -fsSL https://ollama.com/install.sh | sh
}

enable_service_if_available() {
  if ! command -v systemctl >/dev/null 2>&1; then
    echo "systemctl not found; skipping service enable/start."
    return
  fi

  if systemctl list-unit-files ollama.service >/dev/null 2>&1; then
    if systemctl is-active --quiet ollama && systemctl is-enabled --quiet ollama; then
      echo "ollama.service is already enabled and active."
    else
      echo "Enabling and starting ollama.service if needed..."
      sudo systemctl enable --now ollama
    fi
  fi
}

fix_service_path_if_requested() {
  if [[ "${1:-}" != "--fix-service-path" ]]; then
    return
  fi

  echo "Updating ollama.service override to use ${MODEL_DIR}..."
  sudo mkdir -p /etc/systemd/system/ollama.service.d
  sudo tee /etc/systemd/system/ollama.service.d/override.conf >/dev/null <<EOF
[Service]
Environment="OLLAMA_MODELS=${MODEL_DIR}"
Environment="OLLAMA_HOST=${SERVICE_HOST}"
Environment="OLLAMA_KEEP_ALIVE=10m"
Environment="OLLAMA_NO_CLOUD=1"
Environment="OLLAMA_NUM_PARALLEL=1"
EOF
  sudo systemctl daemon-reload
  sudo systemctl restart ollama
}

start_temp_server_if_needed() {
  local status
  local service_env

  if [[ "$HOST" == "$SERVICE_HOST" ]] && command -v systemctl >/dev/null 2>&1; then
    service_env="$(systemctl show ollama --property=Environment --value 2>/dev/null || true)"
    if [[ "$service_env" != *"OLLAMA_MODELS=${MODEL_DIR}"* ]]; then
      echo "ollama.service is not using ${MODEL_DIR}; avoiding the systemd API for pulls."
      echo "Current service environment: ${service_env:-<unset>}"
      status="service-path-mismatch"
    else
      status="$(curl -sS -o /tmp/ollama-tags.json -w '%{http_code}' "http://${HOST}/api/tags" || true)"
    fi
  else
    status="$(curl -sS -o /tmp/ollama-tags.json -w '%{http_code}' "http://${HOST}/api/tags" || true)"
  fi

  if [[ "$status" == "200" ]]; then
    echo "Ollama API healthy at ${HOST}."
    return
  fi

  if [[ "$HOST" != "$SERVICE_HOST" ]]; then
    die "Ollama API at ${HOST} is not healthy (HTTP ${status})."
  fi

  echo "Ollama API at ${SERVICE_HOST} is not healthy (HTTP ${status})."
  echo "Starting a temporary non-systemd Ollama server at ${TEMP_HOST} using ${MODEL_DIR}..."
  HOST="$TEMP_HOST"
  OLLAMA_HOST="$TEMP_HOST" OLLAMA_MODELS="$MODEL_DIR" OLLAMA_NO_CLOUD=1 "$OLLAMA_BIN" serve >/tmp/ollama-temp-serve.log 2>&1 &
  TEMP_PID="$!"
  trap '[[ -n "${TEMP_PID:-}" ]] && kill "$TEMP_PID" >/dev/null 2>&1 || true' EXIT

  for _ in $(seq 1 40); do
    status="$(curl -sS -o /tmp/ollama-tags.json -w '%{http_code}' "http://${HOST}/api/tags" || true)"
    [[ "$status" == "200" ]] && return
    sleep 0.5
  done

  echo "Temporary Ollama log:"
  sed -n '1,120p' /tmp/ollama-temp-serve.log || true
  die "Temporary Ollama API did not become healthy."
}

check_gpu() {
  echo
  echo "GPU check:"
  if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || true
  else
    echo "nvidia-smi not found."
  fi

  local ps_output=""
  local gpu_detected=0
  if ps_output="$(OLLAMA_HOST="$HOST" "$OLLAMA_BIN" ps 2>/dev/null)" && [[ -n "$ps_output" ]]; then
    if printf '%s\n' "$ps_output" | grep -q 'GPU'; then
      echo "Ollama GPU status detected from loaded model."
      gpu_detected=1
    fi
  fi

  if command -v journalctl >/dev/null 2>&1; then
    if journalctl -u ollama --since "1 hour ago" --no-pager 2>/dev/null | grep -Eq 'library=CUDA|CUDA0|NVIDIA'; then
      echo "Ollama CUDA log detected."
    elif [[ "$gpu_detected" -eq 0 ]]; then
      echo "No recent Ollama CUDA log found yet; run a model, then check journalctl -u ollama."
    fi
  fi

  if [[ -n "$ps_output" ]]; then
    echo
    echo "Ollama loaded model status:"
    printf '%s\n' "$ps_output"
  fi
}

pull_models() {
  echo
  echo "Model pull plan:"
  printf '  %s\n' "${MODELS[@]}"
  echo

  mkdir -p "$MODEL_DIR"

  for model in "${MODELS[@]}"; do
    if [[ "$model" =~ (^|:)([7-9]|[1-9][0-9]+)b$ ]]; then
      die "Refusing to pull ${model}; this starter script only pulls sub-7B models."
    fi

    if has_model "$model"; then
      echo "Already installed, skipping: ${model}"
    else
      echo "Pulling: ${model}"
      OLLAMA_HOST="$HOST" "$OLLAMA_BIN" pull "$model"
    fi
  done
}

print_summary() {
  echo
  echo "Summary"
  echo "Ollama version: $("$OLLAMA_BIN" --version)"
  echo "Ollama API used: ${HOST}"
  echo "Ollama model dir: ${MODEL_DIR}"
  echo
  check_gpu
  echo
  echo "Installed models:"
  OLLAMA_HOST="$HOST" "$OLLAMA_BIN" list
  echo
  echo "Recommended default general chat model: qwen3:4b"
  echo "Recommended default coding model: qwen2.5-coder:3b"
}

main() {
  install_ollama_if_missing
  enable_service_if_available
  fix_service_path_if_requested "${1:-}"
  start_temp_server_if_needed
  check_gpu
  pull_models
  print_summary
}

main "$@"
