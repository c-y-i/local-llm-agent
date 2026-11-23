# Windows Setup

English | [简体中文](windows.zh-CN.md)

## Supported Windows Workflow

Windows 10/11 x64 is supported for:

- llama.cpp through `llama-server.exe`
- Ollama
- Claude Code, Codex CLI, and Hermes Agent
- the `llm` Python CLI

vLLM and Strata remain WSL2 workflows. They are not launched natively by the
Windows scripts.

## Requirements

- Python 3.11 or newer
- Git
- CMake
- an NVIDIA driver visible through `nvidia-smi`
- Visual Studio C++ Build Tools and the NVIDIA CUDA Toolkit for a CUDA build
- the agent CLIs you intend to use

Install the agent CLIs separately:

```powershell
# Examples; use each vendor's current installer.
irm https://hermes-agent.nousresearch.com/install.ps1 | iex
```

## Install The Repository

From the repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup\install-llm.ps1 -AddToPath
```

The installer creates:

```text
%USERPROFILE%\LLM\
  models\
  llama.cpp\
  run\
  .venv\
```

It also sets the per-user `OLLAMA_MODELS` variable to
`%USERPROFILE%\LLM\ollama\models\llm` when that variable is not already set.
Restart Ollama after installation so its background app sees the shared model
store.

It also installs `llm.cmd`, `claude-local.cmd`, `codex-local.cmd`, and
`hermes-local.cmd` under `%USERPROFILE%\.local\bin`.

The repository-root `.cmd` launchers work without changing PATH:

```powershell
.\llm.cmd --version
```

## Check And Build

```powershell
.\scripts\setup\check-prereqs.ps1
.\llm.cmd doctor
.\llm.cmd build llama-cpp
```

Force CPU-only:

```powershell
.\llm.cmd build llama-cpp --cuda OFF
```

The build script accepts CUDA builds produced under either:

```text
%USERPROFILE%\LLM\llama.cpp\build\bin\Release\llama-server.exe
%USERPROFILE%\LLM\llama.cpp\build\bin\llama-server.exe
```

Do not use a Linux `llama-server` binary on Windows.

For a prebuilt binary installed elsewhere, set its absolute path:

```powershell
$env:LLAMA_SERVER_BIN = "D:\tools\llama.cpp\llama-server.exe"
```

## Models

Put GGUF files under:

```text
%USERPROFILE%\LLM\models
```

Use the filename without `.gguf` as the model ID:

```powershell
.\llm.cmd models
.\llm.cmd start llama-cpp qwen3.5-4b-official-Q4_K_M
```

## Start An Agent

With the model server running:

```powershell
.\claude-local.cmd
.\codex-local.cmd
.\hermes-local.cmd
```

or use the PATH-installed commands:

```powershell
claude-local
codex-local
hermes-local
```

## Ollama

Install Ollama:

```powershell
.\scripts\setup\install-ollama.ps1
```

Start it from the Start menu or run:

```powershell
ollama serve
```

Then:

```powershell
.\llm.cmd start ollama qwen3.5:9b
```

## Environment Overrides

Windows PowerShell uses the same `.env` file as Linux. Both `$VAR` and `%VAR%`
forms are expanded. Default paths are derived from `%USERPROFILE%`.

Useful overrides:

```dotenv
LLM_ROOT=D:\LLM
LLAMA_CPP_PORT=8080
OLLAMA_HOST=127.0.0.1:11434
```

## Troubleshooting

```powershell
.\llm.cmd doctor
.\llm.cmd status
Get-Content "$env:USERPROFILE\LLM\run\llama-server.log" -Tail 100
Get-NetTCPConnection -LocalPort 8080 -State Listen
```

If a model was downloaded for Linux but references `/home/...`, replace the
absolute path or download it again under `%USERPROFILE%\LLM\models`.

## Dashboard

The dashboard can run natively:

```powershell
python control_panel.py
```

Windows monitoring uses `tasklist`, `nvidia-smi`, and PowerShell CIM data for
CPU/RAM. Dashboard service controls are intentionally disabled on Windows;
use `llm.cmd start` and `llm.cmd stop` instead.
