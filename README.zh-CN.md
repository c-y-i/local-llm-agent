# local-llm-agent

[English](README.md) | 简体中文

在自有硬件上运行本地编码模型，并连接 Claude Code、Codex CLI 或 Hermes Agent。
仓库只保存代码、文档和小型配置；模型权重、引擎构建和运行状态都放在仓库外。

## 参考配置和已验证 Agent

参考配置是 6 GB 显存的 RTX 3050 Laptop GPU。当前流程已在该硬件上完成
端到端验证：

- Claude Code
- Codex CLI
- Hermes Agent

三个 Agent 共同使用的测试后端是 llama.cpp 和官方 Qwen3.5-4B Q4_K_M。
Hermes 还使用官方 Qwen3.5-2B 验证了大上下文窗口。这些模型只是该硬件档位的
示例，不是强制要求；显存和内存更大的机器可以选择更大、更强的模型。

## 当前范围

| 组件 | 状态 | 地址 |
|---|---|---|
| llama.cpp | 主要本地后端 | `http://127.0.0.1:8080` |
| Ollama | 辅助后端和模型存储 | `http://127.0.0.1:11434` |
| Claude Code | 已验证 | llama.cpp 原生，Ollama 通过兼容代理 |
| Codex CLI | 已验证 | llama.cpp Responses provider |
| Hermes Agent | 已验证 | OpenAI 兼容端点 |
| vLLM | 暂缓 | 不属于当前硬件工作流 |
| Strata | 暂缓 | 不属于当前硬件工作流 |

旧的 Cline、Copilot、控制面板、便携启动器、vLLM 和 Strata 文档及截图已暂时
移除。当前文档只描述经过验证的本地 Agent 路径。

## 安装

```bash
./scripts/setup/install-llm.sh
source .venv/bin/activate
llm --version
```

`llm` 需要受管理的 Python 环境；`*-local` Agent 命令会自动激活它。

## 快速开始

先检查依赖、构建 llama.cpp 并准备模型：

```bash
./scripts/setup/check-prereqs.sh
source .venv/bin/activate
llm setup

curl -fL --retry 5 -C - \
  -o ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf.part \
  https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/main/Qwen3.5-4B-Q4_K_M.gguf
mv ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf.part \
  ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf
```

下载约 2.6 GB。更小的 Qwen3.5-2B 下载方式见
[`docs/models.zh-CN.md`](docs/models.zh-CN.md)。还需安装准备使用的
Claude Code、Codex CLI 或 Hermes CLI；`llm doctor` 会检查它们是否存在。

然后启动交互工具：

```bash
llm
```

主菜单会分别显示当前活动模型和可达服务。Ollama 服务运行但未加载模型时显示
为 `ready (idle)`，不会被误认为活动后端。菜单始终默认运行模型，第二项是
浏览已安装模型，第三项是打开 Agent。

菜单还包含停止活动模型和运行时诊断。如果 llama.cpp 已占用 8080 端口，
`llm start` 会询问是否替换。
同一时间只运行一个推理引擎；在 llama.cpp 和 Ollama 之间切换时会自动停止
之前的引擎。

典型双终端流程：

```bash
# 终端 1
source .venv/bin/activate
llm start

# 终端 2，可在任意项目目录中运行
claude-local
# 或
codex-local
# 或
hermes-local
```

`*-local` 命令会保留调用时所在目录，并自动使用正在运行的后端。

## 模型列表

CLI 支持任何兼容的 GGUF 模型。文档中列出的模型只是用于验证参考笔记本
完整流程的示例；用户应根据自己的硬件和质量要求选择模型。

```bash
llm models
llm models --sort name
llm models --json
```

默认显示安装大小并按从小到大自动排列；`llm start` 的模型选择器也会显示大小。

模型文件不得放在仓库中。默认目录：

```text
~/LLM/
  models/        # 共享 GGUF
  llama.cpp/     # 引擎源码和构建
  ollama/        # Ollama 状态和模型链接
  .venv/         # Python 环境
  run/           # 日志和运行状态
```

可在 `.env` 中修改 `LLM_ROOT` 或单独路径，详见
[`docs/backends.zh-CN.md`](docs/backends.zh-CN.md)。

## 上下文

上下文窗口由正在运行的后端决定。Agent 启动器读取服务端实际值，不应再保存
另一份硬编码值。如果 Hermes 存在与服务端冲突的上下文设置，`llm` 会拒绝
启动并提示删除。

llama.cpp 启动菜单会按模型提供上下文选项，也支持手动输入。更大的上下文会
消耗更多显存或内存，详见 [`docs/context-memory.zh-CN.md`](docs/context-memory.zh-CN.md)。

## 文档

| 文档 | 内容 |
|---|---|
| [`docs/cli.zh-CN.md`](docs/cli.zh-CN.md) | `llm` 命令和交互流程 |
| [`docs/agents.zh-CN.md`](docs/agents.zh-CN.md) | Claude Code、Codex CLI、Hermes |
| [`docs/backends.zh-CN.md`](docs/backends.zh-CN.md) | llama.cpp、Ollama、存储和生命周期 |
| [`docs/models.zh-CN.md`](docs/models.zh-CN.md) | 已验证模型和建议 |
| [`docs/context-memory.zh-CN.md`](docs/context-memory.zh-CN.md) | 上下文窗口和 KV cache |
| [`docs/troubleshooting.zh-CN.md`](docs/troubleshooting.zh-CN.md) | 常见问题和诊断 |

在 CLI 展示稳定前，暂不保留截图和媒体文件。
