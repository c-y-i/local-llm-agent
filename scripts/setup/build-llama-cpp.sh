#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

run() {
  echo "+ $*"
  if [[ "$DRY_RUN" != "1" ]]; then
    "$@"
  fi
}

if [[ ! -d "${LLAMA_CPP_ROOT}/src/.git" ]]; then
  run mkdir -p "$LLAMA_CPP_ROOT"
  run git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "${LLAMA_CPP_ROOT}/src"
else
  run git -C "${LLAMA_CPP_ROOT}/src" pull --ff-only
fi

run cmake -B "${LLAMA_CPP_ROOT}/build" -S "${LLAMA_CPP_ROOT}/src" \
  -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release
run cmake --build "${LLAMA_CPP_ROOT}/build" -j"$(nproc)"

echo
echo "llama.cpp build path: ${LLAMA_CPP_ROOT}/build"
