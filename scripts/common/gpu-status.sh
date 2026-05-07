#!/usr/bin/env bash
# Intentionally NOT using `set -e` — many of the checks below (systemctl is-active
# on a stopped service, nvidia-smi when no procs run, etc.) exit non-zero by design.
set -uo pipefail

# One-screen status: GPU, Ollama, llama-server.
# Run this whenever you want to know "what's holding the GPU" or "is anything running".
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env.sh
source "${SCRIPT_DIR}/env.sh"

# --- GPU memory + util -------------------------------------------------------
read -r used free total util gpu_name <<< "$(
  nvidia-smi --query-gpu=memory.used,memory.free,memory.total,utilization.gpu,name \
             --format=csv,noheader,nounits 2>/dev/null \
  | awk -F', ' 'NR==1 {print $1, $2, $3, $4, $5}'
)"
printf '\033[1mGPU\033[0m %s\n' "$gpu_name"
printf '  VRAM : %s / %s MiB used  (%s MiB free)\n' "$used" "$total" "$free"
printf '  Util : %s%%\n' "$util"

# --- Processes holding VRAM --------------------------------------------------
gpu_procs="$(nvidia-smi --query-compute-apps=pid,used_memory,process_name \
                        --format=csv,noheader,nounits 2>/dev/null)"
if [[ -n "$gpu_procs" ]]; then
  printf '  Procs:\n'
  echo "$gpu_procs" | awk -F', ' '{ printf "    %6s MiB  pid=%-7s %s\n", $2, $1, $3 }'
fi

echo

# --- Ollama service state ----------------------------------------------------
if systemctl list-unit-files ollama.service >/dev/null 2>&1; then
  active="$(systemctl is-active ollama 2>/dev/null || true)"
  enabled="$(systemctl is-enabled ollama 2>/dev/null || true)"
  printf '\033[1mOllama\033[0m  service: %s (%s)\n' "$active" "$enabled"
  if [[ "$active" == "active" ]]; then
    if ps_out="$(ollama ps 2>/dev/null)" && [[ "$(echo "$ps_out" | wc -l)" -gt 1 ]]; then
      echo "$ps_out" | awk 'NR>1 { printf "  loaded : %s  (%s)\n", $1, $4 }'
    else
      echo '  loaded : (none)'
    fi
  fi
else
  printf '\033[1mOllama\033[0m  not installed\n'
fi

echo

# --- llama-server processes --------------------------------------------------
ls_pids="$(pgrep -f 'llama-server' 2>/dev/null || true)"
if [[ -n "$ls_pids" ]]; then
  printf '\033[1mllama-server\033[0m\n'
  for pid in $ls_pids; do
    cmdline="$(tr '\0' ' ' < /proc/"$pid"/cmdline 2>/dev/null || true)"
    model="$(echo "$cmdline" | grep -oE '[^[:space:]]+\.gguf' | head -1)"
    port="$(echo "$cmdline" | grep -oE -- '--port [0-9]+' | awk '{print $2}')"
    [[ -z "$port" ]] && port=8080
    printf '  pid=%-7s port=%-5s model=%s\n' "$pid" "$port" "${model:-?}"
  done
else
  printf '\033[1mllama-server\033[0m  not running\n'
fi
