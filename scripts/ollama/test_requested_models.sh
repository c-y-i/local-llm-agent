#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
PROMPT="${1:-Reply in one short sentence: why are small local models useful?}"
MODELS=(
  "qwen3:4b"
  "llama3.2:3b"
  "qwen2.5-coder:3b"
  "phi4-mini"
  "qwen3:1.7b"
)

if ! curl -fsS "http://${HOST}/api/tags" >/dev/null; then
  echo "Ollama API is not healthy at ${HOST}."
  echo "Run ${LOCAL_LLM_AGENT_ROOT}/scripts/setup/configure-ollama.sh first."
  exit 1
fi

echo "Ollama host: ${HOST}"
echo "Prompt: ${PROMPT}"
echo

for model in "${MODELS[@]}"; do
  canonical="$model"
  [[ "$model" != *:* ]] && canonical="${model}:latest"

  if ! OLLAMA_HOST="$HOST" ollama list | awk 'NR > 1 {print $1}' | grep -Fxq -e "$model" -e "$canonical"; then
    echo "=== ${model} ==="
    echo "SKIP: not installed"
    echo
    continue
  fi

  echo "=== ${model} ==="
  MODEL="$model" PROMPT="$PROMPT" HOST="$HOST" python3 - <<'PY'
import json
import os
import subprocess
import sys
import time
import urllib.request

host = os.environ["HOST"]
model = os.environ["MODEL"]
prompt = os.environ["PROMPT"]
payload = {
    "model": model,
    "prompt": prompt,
    "stream": False,
    "think": False,
    "options": {
        "num_predict": 48,
        "temperature": 0.2,
    },
}

started = time.monotonic()
request = urllib.request.Request(
    f"http://{host}/api/generate",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with urllib.request.urlopen(request, timeout=180) as response:
        data = json.loads(response.read().decode("utf-8"))
except Exception as exc:
    print(f"ERROR: {exc}", file=sys.stderr)
    sys.exit(1)

elapsed = time.monotonic() - started
total = data.get("total_duration", 0) / 1_000_000_000
load = data.get("load_duration", 0) / 1_000_000_000
eval_count = data.get("eval_count", 0)
eval_time = data.get("eval_duration", 0) / 1_000_000_000
tokens_per_second = eval_count / eval_time if eval_time else 0
output = data.get("response", "").strip()

print(f"Wall time: {elapsed:.3f}s")
print(f"Ollama total: {total:.3f}s; load: {load:.3f}s; eval: {eval_time:.3f}s")
print(f"Tokens: {eval_count}; speed: {tokens_per_second:.2f} tokens/s")
print("Output:")
print(output)
PY
  echo
done
