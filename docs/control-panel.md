# Control Panel & Monitor

Two single-file Python dashboards — no dependencies beyond stdlib.

| | Control Panel | Monitor |
|---|---|---|
| Script | `control_panel.py` | `monitor.py` |
| Default port | 8766 | 8765 |
| Start / stop / restart services | yes | — |
| Load / unload / pull models | yes | — |
| Read-only status view | yes | yes |

<img src="dashboard.gif" alt="Local LLM Control Panel dashboard" width="720">

## Running

```bash
python3 control_panel.py          # controls  →  http://localhost:8766
python3 monitor.py                # read-only →  http://localhost:8765
```

Monitor is useful on shared or remote machines where you want visibility without exposing service controls.

## What it shows

| Card | Contents |
|---|---|
| Services | ollama, llama-cline, litellm-proxy — status + start / stop / restart |
| GPU | VRAM usage, utilization, temperature |
| System | CPU model, cores, RAM meter |
| Storage | Root disk + Ollama models directory (highlights >85% full) |
| Models | Full Ollama model list with load / unload controls |

## Setup flow

The control panel detects when Ollama isn't running (shows a one-click start banner) and when no models are pulled (shows a curated pull list: qwen3:4b, qwen2.5-coder:3b, llama3.2:1b). Once a model is pulled the panel transitions to the normal view automatically.

## Env vars

| Variable | Default | Effect |
|---|---|---|
| `LLM_DASHBOARD_PORT` | 8766 / 8765 | Override listen port |
| `LLM_DASHBOARD_HOST` | `127.0.0.1` | Override listen address |
| `LLM_MONITOR_CONTROLS` | `1` / `0` | Force controls on or off regardless of script |

```bash
LLM_DASHBOARD_PORT=9000 python3 control_panel.py
LLM_MONITOR_CONTROLS=1  python3 monitor.py      # monitor with controls enabled
```

Controls only accept localhost connections and run as the current user.
