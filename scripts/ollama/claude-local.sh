#!/usr/bin/env bash
set -euo pipefail

PROXY_URL="${ANTHROPIC_BASE_URL:-http://localhost:4000}"
AUTH_TOKEN="${ANTHROPIC_AUTH_TOKEN:-ollama}"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"
SYSTEM_PROMPT="${CLAUDE_LOCAL_SYSTEM_PROMPT:-}"
PREFERRED_MODELS=(
  "qwen2.5-coder:3b"
  "qwen2.5-coder:7b"
  "llama3.2:3b"
  "phi4-mini:latest"
)

has_model_arg() {
  local arg
  for arg in "$@"; do
    [[ "$arg" == "--model" || "$arg" == --model=* ]] && return 0
  done
  return 1
}

proxy_status() {
  if curl -fsS --max-time 2 "${PROXY_URL}/health" >/dev/null 2>&1; then
    printf "ok"
  else
    printf "not responding"
  fi
}

print_model_row() {
  local index="$1"
  local selected="$2"
  local name="$3"
  local marker="$4"
  local model_size="$5"
  local details="$6"
  local prefix="  "

  if [[ "$selected" == "1" ]]; then
    prefix="> "
    printf "\033[7m"
  fi
  printf "%s%2d) %-9s %-28s %-8s %s" "$prefix" "$index" "$marker" "$name" "$model_size" "$details"
  if [[ "$selected" == "1" ]]; then
    printf "\033[0m"
  fi
  printf "\n"
}

render_model_picker() {
  local selected="$1"
  shift
  local -n render_ordered="$1"
  local -n render_running="$2"
  local -n render_size="$3"
  local -n render_meta="$4"

  local i name marker details
  printf "\033[?25l"
  printf "\033[H\033[J"
  echo "Claude local model picker"
  echo "Proxy: ${PROXY_URL} ($(proxy_status))"
  echo
  echo "Loaded models are shown first and marked RUNNING."
  echo "Use ↑/↓ or j/k, Enter to select, q to quit. You can also type a number."
  echo
  for i in "${!render_ordered[@]}"; do
    name="${render_ordered[$i]}"
    if [[ -n "${render_running[$name]:-}" ]]; then
      marker="[RUNNING]"
      details="${render_meta[$name]}"
    else
      marker="         "
      details="installed"
    fi
    if ((i == selected)); then
      print_model_row "$((i + 1))" 1 "$name" "$marker" "${render_size[$name]:-?}" "$details"
    else
      print_model_row "$((i + 1))" 0 "$name" "$marker" "${render_size[$name]:-?}" "$details"
    fi
  done
}

select_model_interactive() {
  local -n interactive_ordered="$1"
  local -n interactive_running="$2"
  local -n interactive_size="$3"
  local -n interactive_meta="$4"
  local selected=0 key rest digits=""

  trap 'printf "\033[?25h\n" >&2' RETURN

  while true; do
    render_model_picker "$selected" interactive_ordered interactive_running interactive_size interactive_meta >&2
    IFS= read -rsn1 key || return 1
    case "$key" in
      $'\x1b')
        IFS= read -rsn2 -t 0.05 rest || rest=""
        case "$rest" in
          "[A") ((selected > 0)) && ((selected--)) ;;
          "[B") ((selected < ${#interactive_ordered[@]} - 1)) && ((selected++)) ;;
        esac
        ;;
      $'\n'|"")
        printf "\033[?25h" >&2
        printf "%s" "${interactive_ordered[$selected]}"
        return 0
        ;;
      j)
        ((selected < ${#interactive_ordered[@]} - 1)) && ((selected++))
        ;;
      k)
        ((selected > 0)) && ((selected--))
        ;;
      q)
        return 1
        ;;
      [0-9])
        digits="${key}"
        while IFS= read -rsn1 -t 0.6 key; do
          [[ "$key" =~ [0-9] ]] || break
          digits+="$key"
        done
        if ((digits >= 1 && digits <= ${#interactive_ordered[@]})); then
          printf "\033[?25h" >&2
          printf "%s" "${interactive_ordered[$((digits - 1))]}"
          return 0
        fi
        ;;
    esac
  done
}

select_model_numbered() {
  local -n ordered_ref="$1"
  local -n is_running_ref="$2"
  local -n size_ref="$3"
  local -n meta_ref="$4"

  {
    echo "Claude local model picker"
    echo "Proxy: ${PROXY_URL} ($(proxy_status))"
    echo
    echo "Loaded models are shown first and marked RUNNING."
    echo
  } >&2

  local i name marker details
  for i in "${!ordered_ref[@]}"; do
    name="${ordered_ref[$i]}"
    if [[ -n "${is_running_ref[$name]:-}" ]]; then
      marker="[RUNNING]"
      details="${meta_ref[$name]}"
    else
      marker="         "
      details="installed"
    fi
    printf "%2d) %-9s %-28s %-8s %s\n" "$((i + 1))" "$marker" "$name" "${size_ref[$name]:-?}" "$details" >&2
  done

  echo >&2
  local choice
  if [[ -t 0 ]]; then
    read -r -p "Select model number [default: 1]: " choice
  else
    choice=""
  fi
  choice="${choice:-1}"
  if [[ "$choice" == "q" || "$choice" == "quit" ]]; then
    return 1
  fi
  if ! [[ "$choice" =~ ^[0-9]+$ ]] || ((choice < 1 || choice > ${#ordered_ref[@]})); then
    echo "Invalid selection: $choice" >&2
    return 1
  fi

  printf "%s" "${ordered_ref[$((choice - 1))]}"
}

select_model() {
  local -a running_names all_names ordered
  local -A is_running size meta seen
  local line name id size_num size_unit processor context until

  if ! command -v ollama >/dev/null 2>&1; then
    echo "ollama is not on PATH" >&2
    return 1
  fi

  while IFS=$'\t' read -r name size_value processor context until; do
    [[ -z "${name:-}" ]] && continue
    running_names+=("$name")
    is_running["$name"]=1
    size["$name"]="$size_value"
    meta["$name"]="${processor:-?}, ctx ${context:-?}, ${until:-loaded}"
  done < <(
    ollama ps | awk 'NR > 1 {
      processor = ""
      for (i = 5; i <= NF - 5; i++) {
        processor = processor (processor ? " " : "") $i
      }
      until = $(NF - 3) " " $(NF - 2) " " $(NF - 1) " " $NF
      print $1 "\t" $3 " " $4 "\t" processor "\t" $(NF - 4) "\t" until
    }'
  )

  while read -r name id size_num size_unit _rest; do
    [[ -z "${name:-}" ]] && continue
    all_names+=("$name")
    size["$name"]="${size_num} ${size_unit}"
  done < <(ollama list | awk 'NR > 1')

  for name in "${running_names[@]}"; do
    [[ -z "$name" ]] && continue
    ordered+=("$name")
    seen["$name"]=1
  done
  for name in "${PREFERRED_MODELS[@]}"; do
    [[ -z "${size[$name]:-}" || -n "${seen[$name]:-}" ]] && continue
    ordered+=("$name")
    seen["$name"]=1
  done
  for name in "${all_names[@]}"; do
    [[ -z "$name" ]] && continue
    [[ -n "${seen[$name]:-}" ]] && continue
    ordered+=("$name")
  done

  if ((${#ordered[@]} == 0)); then
    echo "No Ollama models found. Run: ollama list" >&2
    return 1
  fi

  if [[ -t 0 ]]; then
    select_model_interactive ordered is_running size meta
  else
    select_model_numbered ordered is_running size meta
  fi
}

run_claude() {
  local -a claude_args=()
  if [[ -n "$SYSTEM_PROMPT" ]]; then
    claude_args+=(--system-prompt "$SYSTEM_PROMPT")
  fi
  ANTHROPIC_BASE_URL="$PROXY_URL" \
  ANTHROPIC_AUTH_TOKEN="$AUTH_TOKEN" \
  exec "$CLAUDE_BIN" "${claude_args[@]}" "$@"
}

if has_model_arg "$@"; then
  run_claude "$@"
fi

selected_model="$(select_model)"
echo >&2
echo "Starting Claude Code with ${selected_model}" >&2
echo >&2
run_claude --model "$selected_model" "$@"
