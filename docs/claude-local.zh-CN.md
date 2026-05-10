# claude-local 启动器

[English](claude-local.md) | 简体中文

`claude-local` 是将 Claude Code 指向本地 Ollama 模型的日常启动器。

它为实际的 `claude` 命令设置本地 proxy 环境变量：

```bash
ANTHROPIC_BASE_URL=http://localhost:4000
ANTHROPIC_AUTH_TOKEN=ollama
```

启动器脚本：

```bash
scripts/ollama/claude-local.sh
```

shell 快捷方式示例：

```bash
function claude-local() {
  /media/data/LLM/scripts/ollama/claude-local.sh "$@"
}
```

## 模型选择器

不传 `--model` 参数时会弹出模型选择器：

```bash
claude-local
```

<img src="../media/claude_local_menu.png" alt="claude-local model picker showing loaded Ollama models first" width="720">

选择器会读取：

- `ollama ps`：当前已加载的模型
- `ollama list`：已安装的模型

已加载的模型会排在前面并标记为 `[RUNNING]`。

## 示例

打开选择器：

```bash
claude-local
```

跳过选择器，直接指定模型：

```bash
claude-local --model qwen2.5-coder:3b
```

一次性 prompt：

```bash
claude-local -p "Reply with exactly: ready"
```

## 依赖

Ollama 需要在 `11434` 端口可访问：

```bash
./scripts/ollama/serve.sh
```

Claude Code proxy 需要在 `4000` 端口可访问：

```bash
sudo systemctl start litellm-proxy
curl -s http://localhost:4000/health
```

Proxy 的内部实现见 [`claude-proxy.zh-CN.md`](claude-proxy.zh-CN.md)。
