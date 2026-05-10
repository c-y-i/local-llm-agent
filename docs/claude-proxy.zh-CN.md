# Claude Proxy

[English](claude-proxy.md) | 简体中文

本仓库使用 `scripts/ollama/anthropic-proxy.py`，让 Claude Code 可以通过本地 Ollama 模型工作。

```text
Claude Code -> anthropic-proxy (:4000) -> Ollama (:11434)
```

它并不是完整的 Anthropic API 实现，而是面向 Claude Code 本地工作流的轻量协议转换层。

## 做了什么

- 接收 Anthropic Messages API 请求
- 转换为 Ollama chat 请求
- 默认禁用 thinking / reasoning block
- 清理 Claude Code 与本地模型之间常见的不兼容字段
- 对简单的问候类输出做保护，防止模型伪造 tool-call JSON

## 启动

开发模式：

```bash
python3 scripts/ollama/anthropic-proxy.py
```

服务模式：

```bash
sudo systemctl start litellm-proxy
```

健康检查：

```bash
curl -s http://localhost:4000/health
```

## 与 LiteLLM 的关系

服务名 `litellm-proxy` 是历史遗留名称。当前服务实际运行的是本仓库的 `anthropic-proxy.py`，并非 LiteLLM。保留这个名字是为了兼容已有命令和文档习惯。

## 相关文档

- Claude Code 使用：[`claude-code.zh-CN.md`](claude-code.zh-CN.md)
- `claude-local` 启动器：[`claude-local.zh-CN.md`](claude-local.zh-CN.md)
- Ollama 使用：[`usage-ollama.zh-CN.md`](usage-ollama.zh-CN.md)
