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

## 启动

本节仅适用于便携部署。本机部署请参考 [`usage-ollama.zh-CN.md`](usage-ollama.zh-CN.md) 和 `./scripts/ollama/serve.sh`。

在移动硬盘上的仓库目录中运行：

```bash
cd /path/to/portable-drive/local-llm-agent

# 终端 1：保持便携服务运行
OLLAMA_HOST=127.0.0.1:14514 ./scripts/ollama/portable-llm-launcher.sh
```

然后在另一个终端中：

```bash
OLLAMA_HOST=127.0.0.1:14514 ollama list
OLLAMA_HOST=127.0.0.1:14514 ollama run qwen3:4b
```

脚本职责一览：

| 脚本 | 作用 | 会启动 Ollama？ |
|---|---|---|
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
