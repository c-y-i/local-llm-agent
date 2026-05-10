#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common/env.sh
source "${SCRIPT_DIR}/../common/env.sh"

command_name="${LLM_PORTABLE_COMMAND:-llm-portable}"
shell_rc="${LLM_PORTABLE_SHELL_RC:-${HOME}/.bashrc}"
launcher="${LOCAL_LLM_AGENT_ROOT}/scripts/ollama/llm-portable.sh"
start_marker="# >>> local-llm-agent ${command_name} >>>"
end_marker="# <<< local-llm-agent ${command_name} <<<"
dry_run=0
remove=0

usage() {
  cat <<EOF
Usage: $0 [--dry-run] [--remove]

Install or update the ${command_name} shell function in:
  ${shell_rc}

Environment overrides:
  LLM_PORTABLE_COMMAND   command name to install (default: llm-portable)
  LLM_PORTABLE_SHELL_RC  shell rc file to edit (default: ~/.bashrc)
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

if [[ ! -f "$launcher" ]]; then
  echo "Launcher not found: ${launcher}" >&2
  exit 1
fi

block="$(cat <<EOF
${start_marker}
function ${command_name}() {
  local launcher="${launcher}"
  if [[ ! -x "\$launcher" ]]; then
    echo "${command_name}: portable launcher not found: \$launcher" >&2
    echo "${command_name}: plug in the portable drive, or rerun install-llm-portable-command.sh from its current mount path." >&2
    return 127
  fi
  "\$launcher" "\$@"
}
${end_marker}
EOF
)"

if ((dry_run)); then
  echo "Would update: ${shell_rc}"
  echo
  if ((remove)); then
    echo "Would remove block:"
    echo "  ${start_marker}"
    echo "  ${end_marker}"
  else
    printf '%s\n' "$block"
  fi
  exit 0
fi

mkdir -p "$(dirname "$shell_rc")"
touch "$shell_rc"

tmp="$(mktemp)"
awk -v start="$start_marker" -v end="$end_marker" '
  $0 == start { skip = 1; next }
  $0 == end { skip = 0; next }
  !skip { print }
' "$shell_rc" > "$tmp"

if ((remove)); then
  mv "$tmp" "$shell_rc"
  echo "Removed ${command_name} from ${shell_rc}"
  exit 0
fi

{
  cat "$tmp"
  if [[ -s "$tmp" ]] && [[ "$(tail -c 1 "$tmp")" != "" ]]; then
    echo
  fi
  echo
  printf '%s\n' "$block"
} > "$shell_rc"

rm -f "$tmp"

echo "Installed ${command_name} in ${shell_rc}"
echo "Reload your shell with:"
echo "  source ${shell_rc}"
