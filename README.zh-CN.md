# local-llm-agent

[English](README.md) | 简体中文

本地可部署的 LLM 实验环境：把 llama.cpp、Ollama、模型文件、服务脚本和 Web 控制台都放在同一个目录里，可直接接入 Cline、Claude Code 或 Copilot。

## 快速开始

```bash
./scripts/setup/check-prereqs.sh
./scripts/ollama/serve.sh
python3 control_panel.py   # http://localhost:8766
```

## Agents

### Cline

连接 llama.cpp，直接控制 GGUF 文件和上下文：

| 字段 | 值 |
|---|---|
| API Provider | `OpenAI Compatible` |
| Base URL | `http://127.0.0.1:8080/v1` |
| API Key | `114514` |
| Model ID / Context | `./scripts/llama-cpp/cline-server.sh` 启动时打印 |

也可以直接连 Ollama（`API Provider: Ollama`，Base URL `http://127.0.0.1:11434`）。

<img src="docs/cline_demo.png" alt="Cline running with a local Ollama model" width="720">

完整说明：[`docs/cline.md`](docs/cline.md)

### Claude Code

```bash
./scripts/ollama/serve.sh
sudo systemctl start litellm-proxy
claude-local   # 模型选择器 — 已加载的模型排在最上面，标记为 RUNNING
```

<img src="docs/claude_local_menu.png" alt="claude-local model picker showing loaded Ollama models first" width="720">

完整说明：[`docs/claude-local.md`](docs/claude-local.md)、[`docs/claude-code.md`](docs/claude-code.md)、[`docs/claude-proxy.md`](docs/claude-proxy.md)

### Copilot

```bash
./scripts/ollama/serve.sh
ollama pull qwen2.5-coder:7b
```

然后在 VS Code Copilot Chat 的模型选择器里选本地模型。

<img src="docs/copilot_ollama.png" alt="VS Code Copilot Chat model picker showing local Ollama models" width="720">

完整说明：[`docs/copilot.md`](docs/copilot.md)

## 控制台

`monitor.py`（只读，端口 8765）和 `control_panel.py`（完整控制，端口 8766）是纯 Python stdlib 的 Web 控制台，无需任何依赖。

<img src="docs/control_panel.png" alt="Local LLM Control Panel dashboard" width="720">

**控制台内容：**

| 卡片 | 内容 |
|---|---|
| Services | ollama、llama-cline、litellm-proxy — 启动 / 停止 / 重启 |
| GPU | 显存占用、利用率、温度 |
| System | CPU 型号、核心数、内存使用量 |
| Storage | 根分区 + Ollama 模型目录（>85% 时高亮提示） |
| Models | 已安装的 Ollama 模型列表，支持加载 / 卸载 |

**引导流程：** 控制台会自动检测 Ollama 是否在运行（未运行时显示一键启动按钮），以及是否有已拉取的模型（没有时显示推荐模型列表：qwen3:4b、qwen2.5-coder:3b、llama3.2:1b）。模型拉取完成后自动切换到正常视图。

```bash
python3 monitor.py         # 只读  — http://localhost:8765
python3 control_panel.py   # 完整控制 — http://localhost:8766
LLM_DASHBOARD_PORT=9000 python3 monitor.py   # 自定义端口
```

控制操作只接受本机连接，以当前用户权限运行。

## 目录结构

```text
<parent>/
  local-llm-agent/   # 本仓库
  llama-cpp/         # llama.cpp 源码和构建目录
  Ollama/            # Ollama 模型存储
```

所有路径均可通过环境变量覆盖。大型模型文件（GGUF、Ollama blobs）已加入 `.gitignore`。完整的环境变量说明和服务配置见 [`docs/setup.md`](docs/setup.md)。

## 文档

| 文件 | 内容 |
|---|---|
| [`docs/setup.md`](docs/setup.md) | 目录结构、环境变量、服务和安装流程 |
| [`docs/hardware-matching.md`](docs/hardware-matching.md) | 按硬件选择模型 |
| [`docs/usage-llama-cpp.md`](docs/usage-llama-cpp.md) | llama.cpp CLI/server 用法 |
| [`docs/usage-ollama.md`](docs/usage-ollama.md) | Ollama 服务和 API 用法 |
| [`docs/cline.md`](docs/cline.md) | Cline 集成和故障排查 |
| [`docs/copilot.md`](docs/copilot.md) | Copilot Chat/CLI 连接 Ollama |
| [`docs/claude-local.md`](docs/claude-local.md) | `claude-local` 启动器和模型选择器 |
| [`docs/claude-code.md`](docs/claude-code.md) | Claude Code 通过本地代理连接 Ollama |
| [`docs/claude-proxy.md`](docs/claude-proxy.md) | 本地 Anthropic proxy 原理 |
| [`docs/context-memory.md`](docs/context-memory.md) | 上下文窗口、KV cache、持久记忆 |
| [`docs/models.md`](docs/models.md) | 模型家族及其适用场景 |
| [`docs/maintenance.md`](docs/maintenance.md) | 添加 / 删除 / 检查 / 更新模型 |
| [`docs/tuning.md`](docs/tuning.md) | 参数调整和 Modelfile 工作流 |
