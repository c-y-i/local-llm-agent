#!/usr/bin/env bash
set -euo pipefail

# Restart Ollama as a background process owned by this workspace, with a stable
# log file under $LLM_ROOT/run.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

LOG="${LLM_RUN_DIR}/ollama.log"
PID_FILE="${LLM_RUN_DIR}/ollama.pid"

mkdir -p "$LLM_RUN_DIR"

if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet ollama; then
  echo "Ollama is managed by systemd; use: sudo systemctl restart ollama" >&2
  echo "Logs: journalctl -u ollama -f" >&2
  exit 1
fi

for pid in $(pgrep -x ollama || true); do
  echo "Stopping Ollama PID ${pid}..."
  kill "$pid"
done

for _ in $(seq 1 40); do
  if ! pgrep -x ollama >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done
if pgrep -x ollama >/dev/null 2>&1; then
  echo "Ollama did not stop cleanly." >&2
  exit 1
fi

export OLLAMA_MODELS
export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
export OLLAMA_NO_CLOUD="${OLLAMA_NO_CLOUD:-1}"
export OLLAMA_NUM_PARALLEL="${OLLAMA_NUM_PARALLEL:-1}"

echo "Starting managed Ollama..."
nohup ollama serve >>"$LOG" 2>&1 </dev/null &
pid=$!
echo "$pid" >"$PID_FILE"

port="${OLLAMA_HOST##*:}"
for _ in $(seq 1 80); do
  if curl -fsS --max-time 1 "http://127.0.0.1:${port}/api/version" >/dev/null 2>&1; then
    echo "Ollama ready (PID ${pid})"
    echo "Log: ${LOG}"
    exit 0
  fi
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "Ollama exited during startup; see ${LOG}" >&2
    exit 1
  fi
  sleep 0.25
done

echo "Ollama did not become ready; see ${LOG}" >&2
exit 1
