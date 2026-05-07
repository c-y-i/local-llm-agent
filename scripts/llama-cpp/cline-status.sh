#!/usr/bin/env bash
set -euo pipefail

# Show llama-server context/token/VRAM status for the Cline endpoint.
#
# Usage:
#   cline-status.sh             # once, port 8080
#   cline-status.sh 8081        # once, custom port
#   cline-status.sh 8080 2      # refresh every 2 seconds

HOST="${HOST:-127.0.0.1}"
port="${1:-8080}"
interval="${2:-}"

show_status() {
  python3 - "$HOST" "$port" <<'PY'
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request

host, port = sys.argv[1], sys.argv[2]
base = f"http://{host}:{port}"

def fetch(path):
    with urllib.request.urlopen(base + path, timeout=10) as res:
        return res.read().decode()

def fetch_json(path):
    return json.loads(fetch(path))

def fetch_metrics():
    try:
        text = fetch("/metrics")
    except urllib.error.HTTPError as exc:
        if exc.code == 501:
            return None
        raise
    out = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        match = re.match(r"llamacpp:([^ {]+)(?:\{[^}]*\})?\s+([-+0-9.eE]+)", line)
        if match:
            out[match.group(1)] = float(match.group(2))
    return out

def gpu_line():
    try:
        raw = subprocess.check_output([
            "nvidia-smi",
            "--query-gpu=memory.used,memory.free,utilization.gpu",
            "--format=csv,noheader,nounits",
        ], text=True, stderr=subprocess.DEVNULL).strip().splitlines()[0]
        used, free, util = [part.strip() for part in raw.split(",")]
        return f"GPU: {used} MiB used, {free} MiB free, util {util}%"
    except Exception:
        return "GPU: unavailable"

try:
    slots = fetch_json("/slots")
except Exception as exc:
    print(f"{base}: not reachable ({exc})")
    sys.exit(1)

metrics = fetch_metrics()
n_ctx = max((int(slot.get("n_ctx", 0)) for slot in slots), default=0)
busy = sum(1 for slot in slots if slot.get("is_processing"))

print(f"Endpoint: {base}/v1")
print(gpu_line())
print(f"Slots: {len(slots)} total, {busy} processing, context {n_ctx:,} tokens/slot")

for slot in slots:
    state = "busy" if slot.get("is_processing") else "idle"
    decoded = 0
    for next_token in slot.get("next_token", []) or []:
        decoded += int(next_token.get("n_decoded", 0) or 0)
    print(f"  slot {slot.get('id')}: {state}, decoded_now={decoded}")

if metrics is None:
    print("Metrics: disabled. Restart cline-server.sh from the updated wrapper to enable /metrics.")
else:
    high = int(metrics.get("n_tokens_max", 0))
    pct = (high / n_ctx * 100.0) if n_ctx else 0.0
    kv_ratio = metrics.get("kv_cache_usage_ratio")
    kv_tokens = metrics.get("kv_cache_tokens")
    prompt_total = int(metrics.get("prompt_tokens_total", 0))
    predicted_total = int(metrics.get("tokens_predicted_total", 0))
    prompt_tps = metrics.get("prompt_tokens_seconds", 0.0)
    predicted_tps = metrics.get("predicted_tokens_seconds", 0.0)
    deferred = int(metrics.get("requests_deferred", 0))

    print(f"High-water request: {high:,} tokens ({pct:.1f}% of context)")
    if kv_ratio is not None:
        extra = f", {int(kv_tokens):,} KV tokens" if kv_tokens is not None else ""
        print(f"KV cache: {kv_ratio * 100:.1f}%{extra}")
    print(f"Totals: {prompt_total:,} prompt tokens, {predicted_total:,} generated tokens")
    print(f"Speed: {prompt_tps:.1f} prompt tok/s, {predicted_tps:.1f} generated tok/s")
    if deferred:
        print(f"Deferred requests: {deferred}")
PY
}

if [[ -n "$interval" ]]; then
  while true; do
    clear
    date
    show_status
    sleep "$interval"
  done
else
  show_status
fi
