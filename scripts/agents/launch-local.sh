#!/usr/bin/env bash
set -euo pipefail

# Installed under three names:
#   claude-local, codex-local, hermes-local
invoked_name="$(basename "$0")"
case "$invoked_name" in
  claude-local) agent="claude" ;;
  codex-local) agent="codex" ;;
  hermes-local) agent="hermes" ;;
  *)
    echo "Unsupported launcher name: $invoked_name" >&2
    exit 2
    ;;
esac

resolved="$(readlink -f "$0")"
SCRIPT_DIR="$(cd "$(dirname "$resolved")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

exec "${REPO_ROOT}/llm" agent "$agent" -- "$@"
