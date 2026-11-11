# Agent 兼容性

[English](agents.md) | 简体中文

## 已验证

以下路径已在 6 GB 显存的 RTX 3050 Laptop GPU 上完成本地验证：

| Agent | llama.cpp | Ollama | 状态 |
|---|---|---|---|
| Claude Code | Anthropic Messages API | 兼容代理 | 已验证 |
| Codex CLI | OpenAI Responses API | 内置集成 | 已验证 |
| Hermes Agent | OpenAI Chat Completions | 原生 | 已验证 |

共同端到端测试使用 llama.cpp 和官方 Qwen3.5-4B Q4_K_M。Hermes 还使用官方
Qwen3.5-2B 验证了大上下文窗口。

## 直接命令

```bash
claude-local
codex-local
hermes-local
```

这些命令会：

- 自动激活受管理的虚拟环境；
- 可在任意项目目录运行；
- 保留调用时所在目录；
- 复用已经运行的模型；
- 没有活动模型时，在后台启动首选 llama.cpp 模型；
- 等服务健康后再启动 Agent。

后台 llama.cpp 日志位于 `$LLM_ROOT/run/llama-server.log`。

## Claude Code

llama.cpp 原生提供 Anthropic Messages API：

```bash
claude-local
```

使用 Ollama 时，`llm claude` 会自动启动 Anthropic 兼容代理，并读取模型服务
的实际上下文长度。

## Codex CLI

```bash
codex-local
```

Codex 使用临时的 Responses API provider 配置。本地状态隔离在
`$LLM_ROOT/codex-local`，不会修改现有 `~/.codex` 配置。

## Hermes Agent

```bash
hermes-local
```

Hermes 使用 OpenAI 兼容 provider，状态目录为 `$LLM_ROOT/hermes-local`。

使用 Ollama 时，应选择带明确 renderer/parser、确定性采样和 32K–64K 上下文的
Agent 标签，详见 [`models.zh-CN.md`](models.zh-CN.md#ollama-agent-标签)。
`qwen3.5-2b-official` 和 Huihui 2B Agent 标签均已验证原生及 OpenAI 兼容
工具调用响应。

### 上下文

Hermes 会读取 llama.cpp 服务端的实际上下文窗口。正常使用时不要在 Hermes
`config.yaml` 中设置：

```yaml
model:
  context_length: 65536
  ollama_num_ctx: 65536
```

这些值会覆盖服务端实际值，可能把 256K 强制压到 64K。`llm hermes` 发现冲突
时会拒绝启动。删除方式：

```bash
HERMES_HOME=/home/cy/LLM/hermes-local \
  hermes config unset model.context_length
HERMES_HOME=/home/cy/LLM/hermes-local \
  hermes config unset model.ollama_num_ctx
```

修改后需要重启 Hermes 会话。

### 精简本地配置

Hermes 默认提示和工具在项目内容之前可能占用约 13K token。Skills 使用渐进式
加载：始终只包含简短索引，实际使用时才读取完整 `SKILL.md`。

2B 模型建议使用精简工具集，不要预加载大型 skill：

```bash
hermes-local -t terminal,file,skills,todo,clarify
```

在精简编码会话中应关闭或避免 browser、computer use、delegation、
connections、图片生成、TTS 和 memory 工具。4B 模型余量更多，但专注的工具集
仍然更可靠。

## 安全

Agent 可以修改文件并执行命令。评估小模型时应保留审批提示、使用 Git，并在
分支或可丢弃目录中工作。协议兼容不代表模型能可靠完成多步工具调用。
