# Windows 安装

[English](windows.md) | 简体中文

Windows 10/11 x64 原生支持 llama.cpp、Ollama 和 `llm` CLI，也可启动
Claude Code、Codex CLI 与 Hermes Agent。vLLM 和 Strata 仍建议在 WSL2 中运行。

## 安装

在仓库根目录运行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup\install-llm.ps1 -AddToPath
```

安装脚本会创建 `%USERPROFILE%\LLM`、管理虚拟环境，并安装
`llm.cmd`、`claude-local.cmd`、`codex-local.cmd` 和
`hermes-local.cmd`。

若尚未设置用户级 `OLLAMA_MODELS`，安装器会指向
`%USERPROFILE%\LLM\ollama\models\llm`。安装后需重启 Ollama，使共享模型目录
生效。

## 检查与构建

```powershell
.\scripts\setup\check-prereqs.ps1
.\llm.cmd doctor
.\llm.cmd build llama-cpp
```

强制 CPU 构建：

```powershell
.\llm.cmd build llama-cpp --cuda OFF
```

GGUF 模型放在 `%USERPROFILE%\LLM\models`，文件名去掉 `.gguf` 后即为模型 ID：

```powershell
.\llm.cmd models
.\llm.cmd start llama-cpp qwen3.5-4b-official-Q4_K_M
```

## 启动 Agent

```powershell
.\claude-local.cmd
.\codex-local.cmd
.\hermes-local.cmd
```

安装并启动 Ollama 后：

```powershell
.\scripts\setup\install-ollama.ps1
.\llm.cmd start ollama qwen3.5:9b
```

`.env` 同时支持 `$VAR` 和 `%VAR%` 形式。完整说明见
[English Windows guide](windows.md)。

## 控制面板

```powershell
python control_panel.py
```

Windows 使用 `tasklist`、`nvidia-smi` 和 PowerShell CIM 收集运行状态。为避免
误操作，Windows 控制面板的服务启动/停止按钮保持只读，请使用
`llm.cmd start` 和 `llm.cmd stop`。
