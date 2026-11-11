# llm CLI

[English](cli.md) | 简体中文

`llm` 是模型存储、llama.cpp、Ollama、运行状态和 Agent 启动的控制工具。

## 安装

```bash
./scripts/setup/install-llm.sh
source .venv/bin/activate
llm --version
```

`llm` 需要受管理的虚拟环境。安装后的 `claude-local`、`codex-local` 和
`hermes-local` 会自动激活它。

## 主菜单

```bash
llm
```

标题会分别显示已加载模型和可达服务。Ollama 服务运行但未加载模型时显示为
`ready (idle)`。

操作顺序固定为：

1. 运行模型
2. 浏览已安装模型
3. 打开编码 Agent
4. 停止活动模型
5. 显示运行时和后端状态
6. 查看活动后端日志
7. 管理后端和安装
8. 运行诊断
9. 显示存储位置
10. 退出

## 运行模型

```bash
llm start
llm start llama-cpp qwen3.5-4b-official-Q4_K_M
llm start llama-cpp qwen3.5-4b-official-Q4_K_M --context 65536
llm start llama-cpp qwen3.5-4b-official-Q4_K_M --gpu-layers 24
```

交互式 llama.cpp 启动会显示上下文窗口选择。模型会显示安装大小并自动按
从小到大排序；存在 Qwen3.5-4B 时会标记为推荐默认项。

Ollama：

```bash
llm start ollama qwen3.5-4b-official:latest
```

Ollama 以守护进程方式运行。在交互终端中，`llm start ollama` 加载模型后会在
选择上下文后，在前台持续显示守护进程日志；按 `Ctrl+C` 返回，模型仍保持加载。
Agent 需要另开终端使用 `claude-local`、`codex-local` 或 `hermes-local` 启动。

也可跳过选择器：

```bash
llm start ollama qwen3.5-2b-official:latest --context 131072
OLLAMA_NUM_CTX=131072 llm start ollama
```

修改上下文会卸载并重新加载 Ollama 模型，同时更新标签的 `num_ctx` 并使 Hermes
上下文缓存失效。已经运行的 Hermes 会话需要重启后才能使用新值。

如果 Ollama 尚未运行，`llm start ollama` 会把它作为后台守护进程启动，日志写入
`$LLM_ROOT/run/ollama.log`。

如果 llama.cpp 已在 8080 端口运行模型，`llm start` 会询问是否替换。也可以
直接停止后台服务：

```bash
llm stop
```

同一时间只允许一个推理引擎运行。启动 llama.cpp 会先停止 Ollama 守护进程；
启动 Ollama 会先停止 llama.cpp。直接启动 Agent 时的自动后端选择也遵守此规则。

## 模型列表

```bash
llm models
llm models --backend llama-cpp
llm models --sort name
llm models --json
```

默认按安装大小从小到大自动排序；`--sort name` 改为按名称排序。

## 状态与诊断

```bash
llm status
llm status --json
llm doctor
llm logs
llm logs --backend ollama --lines 100
llm logs --backend llama-cpp --follow
```

- `active`：模型已加载并正在服务。
- `ready`：服务可达，但没有加载模型。
- `offline`：端点不可达。

## Agent

可在任意项目目录运行：

```bash
claude-local
codex-local
hermes-local
```

这些命令会自动激活环境；需要时会在后台启动首选 llama.cpp 模型，并保留调用
时所在目录。

通用流程：

```bash
llm agent
llm agent claude
llm agent codex
llm agent hermes
```

模型已运行时的显式启动形式：

```bash
llm claude --backend llama-cpp --model qwen3.5-4b-official-Q4_K_M
llm codex --backend llama-cpp --model qwen3.5-4b-official-Q4_K_M
llm hermes --backend llama-cpp --model qwen3.5-4b-official-Q4_K_M
```

Agent 自身参数放在 `--` 后：

```bash
llm agent hermes -- -q "Reply with READY" --oneshot -Q
```

## 路径和配置

```bash
llm paths
llm paths --json
llm config
llm config --init
```

默认数据根目录是 `~/LLM`。可在被 Git 忽略的 `.env` 中设置 `LLM_ROOT`
或单独路径。模型文件永远不会进入仓库。

## 后端安装

```bash
llm build llama-cpp --dry-run
llm build llama-cpp
llm install ollama
```

llama.cpp 是主要验证后端，Ollama 是辅助后端和共享模型存储。vLLM 与
Strata 暂缓用于当前硬件工作流。
