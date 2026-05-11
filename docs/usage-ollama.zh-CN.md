# Ollama 用法

[English](usage-ollama.md) | 简体中文

Ollama 是可选的，但对于拉取模型、非 Cline 的日常聊天以及维护共享模型存储来说非常实用。

## 手动启动服务

推荐方式：

```bash
./scripts/ollama/serve.sh
```

然后在另一个终端中：

```bash
ollama list
ollama run qwen3:1.7b
```

不要直接运行裸的 `ollama serve`，除非你同时设置了 `OLLAMA_MODELS`。否则 Ollama 的 daemon 进程可能会使用默认的空模型目录，导致 `ollama run <tag>` 时重新下载模型。

等价的手动方式：

```bash
source ./scripts/common/env.sh
export OLLAMA_MODELS
ollama serve
```

## Portable LLM Launcher

便携部署时使用：

```bash
./scripts/setup/install-portable-ollama-command.sh
portable-ollama serve
```

这个端口可以避开宿主机默认的 Ollama 服务端口。

另开一个终端时使用同一个 `OLLAMA_HOST`：

```bash
portable-ollama list
portable-ollama run qwen3:4b
```

`portable-ollama` 会把 `OLLAMA_MODELS` 指向本仓库同级的 `Ollama/models/llm`，使用 `OLLAMA_HOST=127.0.0.1:14514`，并调用宿主机上的 `ollama` 命令。需要指定可执行文件时，设置 `OLLAMA_BIN=/path/to/ollama`。

Windows：

```bat
scripts\ollama\portable-llm-launcher.cmd
```

详细说明见 [`portable-llm-launcher.zh-CN.md`](portable-llm-launcher.zh-CN.md)。

## 服务管理

systemd 服务是可选的。

配置模型目录：

```bash
./scripts/setup/configure-ollama.sh --dry-run
./scripts/setup/configure-ollama.sh
```

启动与停止：

```bash
sudo systemctl start ollama
sudo systemctl status ollama
sudo systemctl stop ollama
journalctl -u ollama -f
```

## 模型维护

导入 GGUF 文件：

```bash
./scripts/ollama/import-to-ollama.sh my-model my-model:latest
```

检查软链接：

```bash
./scripts/ollama/check-symlinks.sh
```

删除模型：

```bash
./scripts/ollama/remove-model.sh <model-tag>
```

## Agent 工作流

Ollama 可以直接用于聊天，也可以作为 Claude Code proxy 的后端。对于 Cline，推荐仍然使用 llama.cpp server 作为主路径；Ollama 可作为备选。Cline 配置说明见 [`cline.zh-CN.md`](cline.zh-CN.md)。
