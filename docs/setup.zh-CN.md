# Setup

[English](setup.md) | 简体中文

本项目是面向本地化部署的 LLM agent 工作区，支持本机部署和便携部署两种模式。两种模式共用同一套基础目录结构。

```text
<parent>/
  local-llm-agent/
  llama-cpp/
  Ollama/
```

## 路径默认值

所有脚本都会加载 `scripts/common/env.sh`。

| 变量 | 默认值 |
|---|---|
| `LOCAL_LLM_AGENT_ROOT` | 本仓库根目录 |
| `LLAMA_CPP_ROOT` | `$LOCAL_LLM_AGENT_ROOT/../llama-cpp` |
| `OLLAMA_ROOT` | `$LOCAL_LLM_AGENT_ROOT/../Ollama` |
| `OLLAMA_MODELS` | `$OLLAMA_ROOT/models/llm` |
| `LLM_MODELS_DIR` | `$LOCAL_LLM_AGENT_ROOT/models` |
| `LLAMA_CPP_BIN` | `$LLAMA_CPP_ROOT/build/bin/llama-cli` |
| `LLAMA_SERVER_BIN` | `$LLAMA_CPP_ROOT/build/bin/llama-server` |
| `SERVICE_USER` | 运行服务安装脚本的用户 |

如果目录不在默认位置，可以通过设置对应的环境变量覆盖。

## 安装 Ollama

使用本项目前，宿主机上必须先安装 Ollama。

```bash
# Linux / macOS
curl -fsSL https://ollama.com/install.sh | sh

# Raspberry Pi（ARM64）——同一脚本即可，也可手动下载：
curl -L https://ollama.com/download/ollama-linux-arm64 -o ~/ollama
chmod +x ~/ollama
export OLLAMA_BIN=~/ollama   # 或将文件移到 PATH 中的目录
```

Windows：从 https://ollama.com/download 下载安装包。

如果无法进行系统级安装，可将二进制文件下载到任意位置，并通过 `OLLAMA_BIN=/path/to/ollama` 指定。

## 引导式安装

以下为本机部署的安装流程。

检查依赖和路径解析：

```bash
./scripts/setup/check-prereqs.sh
```

构建 llama.cpp：

```bash
./scripts/setup/build-llama-cpp.sh --dry-run
./scripts/setup/build-llama-cpp.sh
```

配置 Ollama 的 systemd override：

```bash
./scripts/setup/configure-ollama.sh --dry-run
./scripts/setup/configure-ollama.sh
sudo systemctl start ollama
```

安装 Cline 使用的 llama.cpp 服务：

```bash
./scripts/setup/install-llama-cline-service.sh --dry-run
./scripts/setup/install-llama-cline-service.sh
sudo systemctl start llama-cline
```

`llama-cline` 默认不启用开机自启，需要手动 start / stop。

便携部署不要安装宿主机服务，除非你确实需要。每台插入此移动硬盘的宿主机执行一次短命令安装脚本，然后启动便携服务：

```bash
./scripts/setup/install-portable-ollama-command.sh
portable-ollama serve
```

安装脚本会在 `~/.local/bin` 中创建软链接。如果 shell 找不到
`portable-ollama`，请在该宿主机上把 `~/.local/bin` 加入 `PATH`，然后打开新终端。

## 目录结构

```text
local-llm-agent/
  models/                 # 本地 GGUF 文件（已加入 .gitignore）
  modelfiles/             # 轻量级 Ollama Modelfile
  scripts/common/         # 环境变量和状态辅助脚本
  scripts/llama-cpp/      # llama.cpp 封装脚本
  scripts/ollama/         # Ollama 共享与维护脚本
  scripts/setup/          # 安装脚本
  systemd/                # 服务模板
  tuning/                 # 个性化构建与对比工具
  docs/                   # 文档
```

重要文档：

- [`context-memory.zh-CN.md`](context-memory.zh-CN.md) — 上下文窗口、KV cache 与持久化记忆
- [`models.zh-CN.md`](models.zh-CN.md) — 各模型系列及适用场景
- [`hardware-matching.zh-CN.md`](hardware-matching.zh-CN.md) — 按硬件配置推荐模型
- [`portable-llm-launcher.zh-CN.md`](portable-llm-launcher.zh-CN.md) — 便携部署说明
- [`cline.zh-CN.md`](cline.zh-CN.md) — Cline 集成说明
- [`copilot.zh-CN.md`](copilot.zh-CN.md) — Copilot Chat/CLI 连接 Ollama

## 服务

本机部署可以使用 `ollama.service`，并配置 `OLLAMA_MODELS` 指向上面的模型目录。

便携部署推荐使用 Portable LLM Launcher，而非服务：

```bash
portable-ollama serve
```

`portable-ollama` 使用宿主机已安装的 `ollama`、本仓库同级的 `Ollama/models/llm` 模型库，以及 `127.0.0.1:14514`。如需指定可执行文件，可设置 `OLLAMA_BIN=/path/to/ollama`。

`llama-cline.service` 由 `systemd/llama-cline.service.in` 模板生成。安装脚本会填入当前仓库路径和 service user，安装至 `/etc/systemd/system/llama-cline.service`，reload systemd，并保持 disabled 状态。

## 模型共享

推荐的存储模式：

```text
models/<name>.gguf                        # 实际的 GGUF 文件
$OLLAMA_MODELS/blobs/sha256-<digest>      # 指向 GGUF 的软链接
```

llama.cpp 直接读取 `models/*.gguf`。Ollama 读取自己的 CAS 路径并通过软链接访问。`scripts/ollama/` 中的辅助脚本负责维护这一关系。

## 依赖

最低可用依赖：

- `git`
- `cmake`
- C/C++ 编译器
- `python3`
- `curl`
- Ollama（如果使用 Ollama 工作流）
- systemd（如果使用服务安装脚本）
- NVIDIA 驱动 / CUDA GPU，或仅 CPU 的 llama.cpp 构建
