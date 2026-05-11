# Portable LLM Launcher

[English](portable-llm-launcher.md) | 简体中文

本项目支持可选的便携部署模式。同一套仓库结构既可以在本机通过 `./scripts/ollama/serve.sh` 运行，也可以放在移动硬盘上在多台主机之间移动使用，同时携带 Ollama 模型存储和可选的操作系统专用 Ollama 二进制文件。

移动硬盘上不应该安装 systemd 服务——服务属于宿主机配置；前台启动器更适合在多台电脑间移动使用。

## 哪些部分是便携的

```text
<portable-drive>/
  local-llm-agent/
  Ollama/models/llm/
  bin/ollama/linux-amd64/ollama
  bin/ollama/darwin-arm64/ollama
  bin/ollama/windows-amd64/ollama.exe
```

- `Ollama/models/llm/` — 便携模型库
- `bin/ollama/<os>-<arch>/ollama[.exe]` — 可选的便携 Ollama 二进制文件
- `local-llm-agent/scripts/ollama/portable-llm-launcher.*` — 使用便携模型存储启动 Ollama

便携二进制文件仅适用于匹配的操作系统和 CPU 架构。例如，Linux x86_64 的二进制文件可以在大多数 Linux x86_64 台式机和笔记本上运行，但不能用于 Windows、macOS 或 ARM 机器。在其他宿主机上，可以将匹配的二进制文件复制到 `bin/ollama/<os>-<arch>/` 目录，也可以在宿主机上安装 Ollama 并继续使用同一个便携模型存储。

支持的启动目标：

| 宿主机 | 启动器 | 二进制文件位置 |
|---|---|---|
| Linux x86_64 | `portable-llm-launcher.sh` | `bin/ollama/linux-amd64/ollama` |
| Linux ARM64 | `portable-llm-launcher.sh` | `bin/ollama/linux-arm64/ollama` |
| macOS Intel | `portable-llm-launcher.sh` | `bin/ollama/darwin-amd64/ollama` |
| macOS Apple Silicon | `portable-llm-launcher.sh` | `bin/ollama/darwin-arm64/ollama` |
| Windows x86_64 | `portable-llm-launcher.cmd` 或 `.ps1` | `bin/ollama/windows-amd64/ollama.exe` |
| Windows ARM64 | `portable-llm-launcher.cmd` 或 `.ps1` | `bin/ollama/windows-arm64/ollama.exe` |

## 添加便携 Ollama 二进制文件

在已经安装并能正常运行 `ollama` 的机器上：

```bash
./scripts/ollama/install-portable-llm-binary.sh
```

也可以复制指定的二进制文件：

```bash
./scripts/ollama/install-portable-llm-binary.sh --from /usr/local/bin/ollama
```

如果已有其他操作系统的二进制文件，可以提前放入对应位置：

```bash
./scripts/ollama/install-portable-llm-binary.sh --from ./ollama.exe --os windows --arch amd64
```

## 启动

本节仅适用于便携部署。本机部署请参考 [`usage-ollama.zh-CN.md`](usage-ollama.zh-CN.md) 和 `./scripts/ollama/serve.sh`。

日常便携使用只需要两个命令：

```bash
# 终端 1：保持便携服务运行
llm-portable

# 终端 2：连接这个便携服务
llm-ollama list
llm-ollama run qwen3:4b
```

### 完整流程

在移动硬盘上的仓库目录中运行：

```bash
cd /path/to/portable-drive/local-llm-agent

# 可选：将宿主机上的 Ollama 二进制文件复制到移动硬盘
# 这一步不会启动 Ollama
./scripts/ollama/install-portable-llm-binary.sh

# 首次使用时安装快捷命令
./scripts/setup/install-llm-portable-command.sh
source ~/.bashrc

# 在 127.0.0.1:14514 启动便携 Ollama 服务
llm-portable
```

然后在另一个终端中：

```bash
llm-ollama list
llm-ollama run qwen3:4b
```

脚本职责一览：

| 脚本 | 作用 | 会启动 Ollama？ |
|---|---|---|
| `install-portable-llm-binary.sh` | 将 Ollama 可执行文件复制到 `../bin/ollama/<os>-<arch>/` | 不会 |
| `install-llm-portable-command.sh` | 在 `~/.bashrc` 中添加或更新 `llm-portable` 和 `llm-ollama` 函数 | 不会 |
| `llm-portable.sh` / `llm-portable` | 使用 `OLLAMA_HOST=127.0.0.1:14514` 启动便携 Ollama 服务 | 会 |
| `llm-ollama.sh` / `llm-ollama` | 使用 `OLLAMA_HOST=127.0.0.1:14514` 执行 Ollama CLI 命令 | 不会 |
| `portable-llm-launcher.sh` | 底层启动器；除非设置 `OLLAMA_HOST`，否则默认使用 `11434` | 会 |

### 快捷命令说明

`install-llm-portable-command.sh` 会在 `~/.bashrc` 中添加或更新 `llm-portable` 和 `llm-ollama` 两个函数，并写入当前仓库路径。因此克隆或拉取到移动硬盘后，请从移动硬盘上的仓库目录运行此脚本。

如果移动硬盘被拔出，shell 函数仍会保留在 `~/.bashrc` 中，但不会影响 shell 启动。只有在实际执行 `llm-portable` 时才会检查路径。如果启动器不存在，它会提示你重新插入移动硬盘，或从新的挂载路径重新运行安装脚本。

预览将要写入的 shell 函数而不实际修改 `~/.bashrc`：

```bash
./scripts/setup/install-llm-portable-command.sh --dry-run
```

移除 shell 函数：

```bash
./scripts/setup/install-llm-portable-command.sh --remove
source ~/.bashrc
```

也可以直接运行封装脚本：

```bash
./scripts/ollama/llm-portable.sh
```

`llm-portable.sh` 是日常使用的简洁封装，默认使用 `OLLAMA_HOST=127.0.0.1:14514`，以避免和 Ollama 默认端口 `11434` 冲突。

安装脚本写入的 shell 函数大致如下：

```bash
function llm-portable() {
  /path/to/portable-drive/local-llm-agent/scripts/ollama/llm-portable.sh "$@"
}

function llm-ollama() {
  /path/to/portable-drive/local-llm-agent/scripts/ollama/llm-ollama.sh "$@"
}
```

### 直接运行底层启动器

大多数用户应使用 `llm-portable` 和 `llm-ollama`。底层启动器默认仍使用 `11434`，除非显式设置 `OLLAMA_HOST`：

```bash
OLLAMA_HOST=127.0.0.1:14514 ./scripts/ollama/portable-llm-launcher.sh
```

Windows 命令提示符：

```bat
cd /d X:\local-llm-agent
scripts\ollama\portable-llm-launcher.cmd
```

Windows PowerShell：

```powershell
cd X:\local-llm-agent
.\scripts\ollama\portable-llm-launcher.ps1
```

无论哪种启动方式，都需要使用同一个 `OLLAMA_HOST` 来访问：

```bash
OLLAMA_HOST=127.0.0.1:11434 ollama list
OLLAMA_HOST=127.0.0.1:11434 ollama run qwen3:4b
```

如果宿主机已有 Ollama 占用 `11434`，请换一个端口：

```bash
OLLAMA_HOST=127.0.0.1:14514 ./scripts/ollama/portable-llm-launcher.sh
```

Windows PowerShell：

```powershell
$env:OLLAMA_HOST="127.0.0.1:14514"
.\scripts\ollama\portable-llm-launcher.ps1
```

Linux/macOS 已安装辅助命令时，使用：

```bash
llm-ollama list
llm-ollama run qwen3:30b
```

未安装辅助命令时，继续显式指定同一个端口：

```bash
OLLAMA_HOST=127.0.0.1:14514 ollama list
OLLAMA_HOST=127.0.0.1:14514 ollama run qwen3:30b
```

## 模型选择

在未知或配置较低的机器上优先使用小模型：

```bash
ollama run qwen3:4b
ollama run llama3.2:3b
ollama run qwen2.5-coder:3b
```

只有在 RAM 或 VRAM 充足的机器上再使用较大的模型：

```bash
ollama run qwen3:14b
ollama run qwen3:30b
ollama run gemma3:12b
```

硬件分级和模型选择参考 [`hardware-matching.zh-CN.md`](hardware-matching.zh-CN.md)。
