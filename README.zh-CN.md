# local-llm-agent

[English](README.md) | 简体中文

本地化部署的 LLM agent 工作区——在自有硬件上运行模型，对接 agent 工作流。数据完全自主可控，无 token 限制，隐私安全。

## 快速开始

```bash
./scripts/setup/check-prereqs.sh       # 检查依赖项
./scripts/setup/configure-ollama.sh    # 配置 Ollama（仅首次执行）

./scripts/ollama/serve.sh              # 本机 Ollama，127.0.0.1:11434
ollama run qwen3:4b
```

便携硬盘用户可在每台宿主机上执行一次 `./scripts/setup/install-portable-ollama-command.sh`，
然后使用 `portable-ollama serve` 和 `portable-ollama run qwen3:4b`。完整说明见
[`docs/portable-llm-launcher.zh-CN.md`](docs/portable-llm-launcher.zh-CN.md)。

## Agent 集成

### Cline

连接 llama.cpp，直接管理 GGUF 文件和上下文：

| 配置项 | 参数值 |
|---|---|
| API Provider | `OpenAI Compatible` |
| Base URL | `http://127.0.0.1:8080/v1` |
| API Key | `114514` |
| Model ID / Context | `./scripts/llama-cpp/cline-server.sh` 启动时会打印 |

也可以直接对接 Ollama（`API Provider: Ollama`，Base URL `http://127.0.0.1:11434`）。

<img src="media/cline_demo.png" alt="Cline running with a local Ollama model" width="720">

完整说明：[`docs/cline.zh-CN.md`](docs/cline.zh-CN.md)

### Claude Code

```bash
./scripts/ollama/serve.sh
sudo systemctl start litellm-proxy
claude-local   # 模型选择器 — 已加载的模型置顶，标记为 RUNNING
```

<img src="media/claude_local_menu.png" alt="claude-local model picker showing loaded Ollama models first" width="720">

完整说明：[`docs/claude-local.zh-CN.md`](docs/claude-local.zh-CN.md)、[`docs/claude-code.zh-CN.md`](docs/claude-code.zh-CN.md)、[`docs/claude-proxy.zh-CN.md`](docs/claude-proxy.zh-CN.md)

### Copilot

```bash
./scripts/ollama/serve.sh
ollama pull qwen2.5-coder:7b
```

然后在 VS Code Copilot Chat 的模型选择器中即可看到本地模型。

<img src="media/copilot_ollama.png" alt="VS Code Copilot Chat model picker showing local Ollama models" width="720">

完整说明：[`docs/copilot.zh-CN.md`](docs/copilot.zh-CN.md)

## 仪表盘

纯 Python 标准库实现，无任何外部依赖。

### 控制面板

完整服务与模型控制，访问 `http://localhost:8766`。

```bash
python3 control_panel.py
```

<img src="media/dashboard.gif" alt="Local LLM Control Panel dashboard" width="720">

### 监控面板

只读状态视图，访问 `http://localhost:8765`

```bash
python3 monitor.py
```

完整说明：[`docs/control-panel.zh-CN.md`](docs/control-panel.zh-CN.md)

## 目录结构

```text
<parent>/
  local-llm-agent/   # 本仓库
  llama-cpp/         # llama.cpp 源码及构建目录
  Ollama/            # Ollama 模型存储
```

所有路径均可通过环境变量覆盖。大型模型文件（GGUF、Ollama blobs）已加入 `.gitignore`。完整的环境变量说明与服务配置见 [`docs/setup.zh-CN.md`](docs/setup.zh-CN.md)。

## 文档索引

| 文档 | 说明 |
|---|---|
| [`docs/setup.zh-CN.md`](docs/setup.zh-CN.md) | 目录结构、环境变量、服务配置与安装流程 |
| [`docs/control-panel.zh-CN.md`](docs/control-panel.zh-CN.md) | 控制面板与监控面板 — 使用说明与环境变量 |
| [`docs/hardware-matching.zh-CN.md`](docs/hardware-matching.zh-CN.md) | 按硬件配置推荐模型 |
| [`docs/portable-llm-launcher.zh-CN.md`](docs/portable-llm-launcher.zh-CN.md) | 便携式 LLM 启动器：本机/便携模式用法 |
| [`docs/usage-llama-cpp.zh-CN.md`](docs/usage-llama-cpp.zh-CN.md) | llama.cpp CLI/服务端用法 |
| [`docs/usage-ollama.zh-CN.md`](docs/usage-ollama.zh-CN.md) | Ollama 服务与 API 用法 |
| [`docs/cline.zh-CN.md`](docs/cline.zh-CN.md) | Cline 集成与故障排查 |
| [`docs/copilot.zh-CN.md`](docs/copilot.zh-CN.md) | Copilot Chat/CLI 连接 Ollama |
| [`docs/claude-local.zh-CN.md`](docs/claude-local.zh-CN.md) | `claude-local` 启动器和模型选择器 |
| [`docs/claude-code.zh-CN.md`](docs/claude-code.zh-CN.md) | Claude Code CLI 连接 Ollama |
| [`docs/claude-proxy.zh-CN.md`](docs/claude-proxy.zh-CN.md) | 本地 Anthropic proxy 原理 |
| [`docs/context-memory.zh-CN.md`](docs/context-memory.zh-CN.md) | 上下文窗口、KV cache、持久化记忆 |
| [`docs/models.zh-CN.md`](docs/models.zh-CN.md) | 各模型系列及适用场景 |
| [`docs/maintenance.zh-CN.md`](docs/maintenance.zh-CN.md) | 模型的添加/删除/检查/更新 |
| [`docs/tuning.zh-CN.md`](docs/tuning.zh-CN.md) | 参数调优与 Modelfile 工作流 |
