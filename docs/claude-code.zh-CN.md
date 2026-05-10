# Claude Code

[English](claude-code.md) | 简体中文

Claude Code CLI 可以通过本地 Anthropic 兼容 proxy 连接 Ollama。

```text
Claude Code CLI -> anthropic-proxy (:4000) -> Ollama (:11434)
```

本仓库使用 `scripts/ollama/anthropic-proxy.py`，它会将 Anthropic Messages API 转换为 Ollama chat API，并处理 Claude Code 常见的 thinking / tool-call 兼容问题。

## 快速启动

Ollama：

```bash
./scripts/ollama/serve.sh
```

Proxy：

```bash
sudo systemctl start litellm-proxy
```

使用本地 Claude Code：

```bash
claude-local
```

完整启动器说明见 [`claude-local.zh-CN.md`](claude-local.zh-CN.md)。

## 安装 proxy 服务

```bash
./scripts/ollama/install-claude-proxy-service.sh
```

服务名历史上叫 `litellm-proxy`，但现在实际运行的是 `anthropic-proxy.py`，并非 LiteLLM。

常用命令：

```bash
sudo systemctl start litellm-proxy
sudo systemctl status litellm-proxy
sudo systemctl stop litellm-proxy
journalctl -u litellm-proxy -f
```

## 测试

检查 proxy：

```bash
curl -s http://localhost:4000/health
```

一次性测试：

```bash
ANTHROPIC_BASE_URL=http://localhost:4000 \
ANTHROPIC_AUTH_TOKEN=ollama \
claude --model qwen2.5-coder:3b -p "Reply with exactly: ready"
```

## 常见问题

| 问题 | 处理方法 |
|---|---|
| `4000` 端口 `Connection refused` | 启动 `litellm-proxy` |
| `11434` 端口 `Connection refused` | 启动 Ollama |
| `does not support thinking` | 确认走的是 `anthropic-proxy.py` |
| tool call 输出异常 | 换用更适合工具调用的 coder 模型 |

相关文档：

- Proxy 内部实现：[`claude-proxy.zh-CN.md`](claude-proxy.zh-CN.md)
- Cline 配置：[`cline.zh-CN.md`](cline.zh-CN.md)
- Copilot + Ollama：[`copilot.zh-CN.md`](copilot.zh-CN.md)
