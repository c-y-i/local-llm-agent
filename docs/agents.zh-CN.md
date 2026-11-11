# Agent 框架兼容性

[English](agents.md) | 简体中文

本仓库支持让 Claude Code、Codex CLI 和 Hermes Agent 使用同一套本地模型服务。
不同框架使用不同 API：

日常使用：

```bash
llm start       # 选择后端和已有模型
llm agent       # 选择 Claude、Codex 或 Hermes
```

| 框架 | 所需协议 | llama.cpp | vLLM | Strata | Ollama |
|---|---|---|---|---|---|
| Claude Code | Anthropic Messages | 原生 | 原生 | 原生 | 兼容代理 |
| Codex CLI | OpenAI Responses | 新版构建 | 原生 | 原生 | 内置 OSS provider |
| Hermes Agent | OpenAI Chat Completions | 原生 | 原生 | 原生 | 原生 |

## Claude Code

```bash
llm claude --backend llama-cpp --model qwen3.5-4b
```

## Codex CLI

```bash
llm codex --backend llama-cpp --model qwen3.5-4b
llm codex --backend vllm --model Qwen3.5-4B
llm codex --backend strata --model q2_0
llm codex --backend ollama --model qwen3.5:4b
```

自定义 Codex provider 使用 Responses API。启动器会自动写入 provider、
`wire_api="responses"`、API key 环境变量、模型和默认 32K 上下文。

## Hermes Agent

```bash
llm hermes --backend llama-cpp --model qwen3.5-4b
```

启动器会设置：

```text
OPENAI_BASE_URL=http://127.0.0.1:8080/v1
OPENAI_API_KEY=local
provider=main
```

Agent 可以修改文件并执行命令。使用 Git 和审批模式，不要让不可靠的小模型在
没有备份的目录中自动执行任务。
