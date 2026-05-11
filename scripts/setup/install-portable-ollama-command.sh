#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

command_name="${PORTABLE_OLLAMA_COMMAND:-portable-ollama}"
bin_dir="${PORTABLE_OLLAMA_BIN_DIR:-${HOME}/.local/bin}"
target="${bin_dir}/${command_name}"
source_cmd="${LOCAL_LLM_AGENT_ROOT}/scripts/ollama/portable-ollama"
dry_run=0
remove=0

usage() {
  cat <<EOF
Usage: $0 [--dry-run] [--remove]

Install or remove a PATH command for the repo-local portable Ollama wrapper.

Defaults:
  command: ${command_name}
  target : ${target}
  source : ${source_cmd}

Environment overrides:
  PORTABLE_OLLAMA_COMMAND  command name to install
  PORTABLE_OLLAMA_BIN_DIR  install directory, default ~/.local/bin
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      dry_run=1
      shift
      ;;
    --remove)
      remove=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! "$command_name" =~ ^[A-Za-z_][A-Za-z0-9_-]*$ ]]; then
  echo "Invalid command name: ${command_name}" >&2
  exit 2
fi

if [[ ! -x "$source_cmd" ]]; then
  echo "portable-ollama wrapper not executable: ${source_cmd}" >&2
  exit 1
fi

if ((dry_run)); then
  if ((remove)); then
    echo "Would remove: ${target}"
  else
    echo "Would install symlink:"
    echo "  ${target} -> ${source_cmd}"
  fi
  exit 0
fi

if ((remove)); then
  if [[ -L "$target" && "$(readlink "$target")" == "$source_cmd" ]]; then
    rm -f "$target"
    echo "Removed ${target}"
  else
    echo "Not removing ${target}; it is not a symlink to ${source_cmd}" >&2
    exit 1
  fi
  exit 0
fi

mkdir -p "$bin_dir"
if [[ -e "$target" && ! -L "$target" ]]; then
  echo "Refusing to replace non-symlink: ${target}" >&2
  exit 1
fi

if [[ -L "$target" && "$(readlink "$target")" != "$source_cmd" ]]; then
  echo "Refusing to replace symlink with different target: ${target} -> $(readlink "$target")" >&2
  exit 1
fi

ln -sfn "$source_cmd" "$target"

echo "Installed ${command_name}:"
echo "  ${target} -> ${source_cmd}"
echo
echo "If your shell cannot find it, add this to PATH:"
echo "  export PATH=\"${bin_dir}:\$PATH\""
