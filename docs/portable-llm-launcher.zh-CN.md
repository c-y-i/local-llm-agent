# Portable LLM Launcher

[English](portable-llm-launcher.md) | 简体中文

本项目支持可选的便携部署模式。同一套仓库结构既可以在本机通过 `./scripts/ollama/serve.sh` 运行，也可以放在移动硬盘上在多台主机之间移动使用，同时携带 Ollama 模型存储。

移动硬盘上不应该安装 systemd 服务——服务属于宿主机配置；前台启动器更适合在多台电脑间移动使用。

## 哪些部分是便携的

```text
<portable-drive>/
  local-llm-agent/
  Ollama/models/llm/
```

- `Ollama/models/llm/` — 便携模型库
- `local-llm-agent/scripts/ollama/portable-llm-launcher.*` — 使用便携模型存储启动 Ollama
- 启动器使用宿主机的 `ollama` 命令；如需指定可执行文件，可设置 `OLLAMA_BIN=/path/to/ollama`

## 前置条件

启动器使用**宿主机**上安装的 `ollama` 二进制文件——它本身不携带该文件。每台新主机都需要先安装 Ollama，再运行启动器：

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

## 启动

本节仅适用于便携部署。本机部署请参考 [`usage-ollama.zh-CN.md`](usage-ollama.zh-CN.md) 和 `./scripts/ollama/serve.sh`。

在移动硬盘上的仓库目录中运行：

```bash
cd /path/to/portable-drive/local-llm-agent

# 每台插入此移动硬盘的宿主机执行一次。
./scripts/setup/install-portable-ollama-command.sh

# 终端 1：保持便携服务运行
portable-ollama serve
```

安装脚本会在 `~/.local/bin` 中创建软链接。如果 shell 找不到
`portable-ollama`，请在该宿主机上把 `~/.local/bin` 加入 `PATH`，然后打开新终端。

然后在另一个终端中：

```bash
portable-ollama list
portable-ollama run <model>
```

脚本职责一览：

| 脚本 | 作用 | 会启动 Ollama？ |
|---|---|---|
| `portable-ollama` | 对便携模型库执行 Ollama 命令；`serve` 会启动便携服务 | 仅 `serve` 会 |
| `install-portable-ollama-command.sh` | 将 `portable-ollama` 软链接到 `~/.local/bin` | 不会 |
| `portable-llm-launcher.sh` | 使用本仓库同级的 `Ollama/models/llm` 模型库启动 Ollama | 会 |
| `portable-llm-launcher.ps1` / `.cmd` | Windows 下同一便携模型库布局的启动器 | 会 |

### 直接运行底层启动器

启动器默认使用 `127.0.0.1:11434`，除非显式设置 `OLLAMA_HOST`。如果宿主机已有 Ollama 占用 `11434`，请换一个端口：

```bash
OLLAMA_HOST=127.0.0.1:14514 ./scripts/ollama/portable-llm-launcher.sh
```

Windows 命令提示符：

```bat
cd /d X:\local-llm-agent
set OLLAMA_HOST=127.0.0.1:14514
scripts\ollama\portable-llm-launcher.cmd
```

Windows PowerShell：

```powershell
cd X:\local-llm-agent
$env:OLLAMA_HOST="127.0.0.1:14514"
.\scripts\ollama\portable-llm-launcher.ps1
```

无论哪种启动方式，都需要使用同一个 `OLLAMA_HOST` 来访问：

```bash
OLLAMA_HOST=127.0.0.1:14514 ollama list
OLLAMA_HOST=127.0.0.1:14514 ollama run <model>
```

## 模型选择

```bash
ollama run <model>
```

硬件分级和模型选择参考 [`hardware-matching.zh-CN.md`](hardware-matching.zh-CN.md)。
