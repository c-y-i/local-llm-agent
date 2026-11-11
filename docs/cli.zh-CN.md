# llm CLI

[English](cli.md) | 简体中文

`llm` 是仓库的统一命令入口，用于查看路径、诊断环境、安装引擎、列出模型、
启动服务以及运行 Agent。

## 日常使用

```bash
llm
```

交互菜单将概念分为：

- **模型/后端**：选择要启动的引擎和已有模型
- **Agent**：模型运行后选择 Claude Code、Codex 或 Hermes
- **运行时**：状态、路径和安装检查

交互选择后端和已有模型：

```bash
llm setup
llm start
```

在另一个终端为正在运行的模型选择 Agent：

```bash
llm agent
```

启动器会自动填入后端、模型 ID、endpoint 和协议。脚本仍可使用显式参数。

## 安装

```bash
./scripts/setup/install-llm.sh
source .venv/bin/activate
llm --version
```

每个新 shell 都必须先激活受管理的虚拟环境。

安装器还会创建直接启动本地 Agent 的命令：

```bash
claude-local
codex-local
hermes-local
```

它们内部调用 `llm agent <name>`，因此与 `llm` 使用相同的后端、模型选择和
隔离配置。

## 存储路径

```bash
llm paths
llm paths --json
llm config
llm config --init
```

默认所有重型文件都放在 `~/LLM`，可通过 `.env` 中的 `LLM_ROOT` 修改。

## 诊断

```bash
llm doctor
llm status
llm models
```

`llm status` 会探测 llama.cpp、vLLM、Strata 和 Ollama。

## 构建与安装

```bash
llm build llama-cpp --dry-run
llm build llama-cpp
llm build llama-cpp --cuda OFF
llm install vllm
llm install ollama
```

vLLM 会安装在 `~/LLM/.venv`，不会写入 Git 仓库。

## 启动模型

```bash
llm start
llm start llama-cpp qwen3.5-4b --context 32768
llm start vllm Qwen/Qwen3.5-4B
llm start strata q2_0 --family qwen
llm start ollama
```

`llm serve` 是 `llm start` 的兼容别名。

## 选择 Agent

```bash
llm agent
llm agent claude
llm agent codex
llm agent hermes
```

`llm agent` 会自动读取当前后端和模型；如果有多个后端在运行，会提示选择。

需要传递 Agent 自身参数时，在这些参数前加 `--`：

```bash
llm agent hermes --model qwen3.5-4b-official:latest -- \
  -q "Reply with exactly READY" --oneshot -Q
```

## Claude Code

```bash
llm claude --backend llama-cpp --model qwen3.5-4b
llm claude --backend vllm --model Qwen3.5-4B
llm claude --backend strata --model q2_0
llm claude --backend ollama --model qwen2.5-coder:3b
```

未指定 `--backend` 时会自动检测正在运行的后端。

## Codex CLI

```bash
llm codex --backend llama-cpp --model qwen3.5-4b
llm codex --backend vllm --model Qwen3.5-4B
llm codex --backend strata --model q2_0
llm codex --backend ollama --model qwen3.5:4b
```

llama.cpp、vLLM、Strata 使用 OpenAI Responses API；Ollama 使用 Codex 内置的
本地 provider。可通过 `--context` 修改默认 32K 上下文。

## Hermes Agent

```bash
llm hermes --backend llama-cpp --model qwen3.5-4b
llm hermes --backend vllm --model Qwen3.5-4B
llm hermes --backend strata --model q2_0
llm hermes --backend ollama --model qwen3.5:4b
```

Hermes 使用 OpenAI 兼容的自定义 endpoint；启动器会设置
`OPENAI_BASE_URL` 和 `OPENAI_API_KEY`。
