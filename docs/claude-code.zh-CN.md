# Claude Code 连接本地模型

[English](claude-code.md) | 简体中文

Claude Code 使用 Anthropic Messages API。新版 llama.cpp、vLLM 和 Strata
原生实现该接口，因此不需要代理。Ollama 仍通过本仓库的兼容代理连接。

| 后端 | Claude Code 地址 | 兼容方式 |
|---|---|---|
| llama.cpp | `http://127.0.0.1:8080` | 原生 `/v1/messages` |
| vLLM | `http://127.0.0.1:8000` | 原生 `/v1/messages` |
| Strata | `http://127.0.0.1:8082` | 原生 `/v1/messages` |
| Ollama | `http://127.0.0.1:4000` | 代理到 Ollama `:11434` |

## 通用启动器

```bash
./scripts/claude/claude-local.sh --backend llama-cpp --model <model>
./scripts/claude/claude-local.sh --backend vllm --model <served-model-id>
./scripts/claude/claude-local.sh --backend strata --model <model-id>
./scripts/claude/claude-local.sh --backend ollama --model <ollama-tag>
```

如果 `claude` 不在 `PATH` 中，请先安装官方 Claude Code CLI：
<https://code.claude.com/docs/en/setup>

省略 `--backend` 时，启动器按 llama.cpp、vLLM、Strata、Ollama proxy 的顺序
检测。使用 `--check` 可在不启动 Claude Code 的情况下验证后端。

启动器默认设置 `CLAUDE_CODE_MAX_CONTEXT_TOKENS=32768`，避免 Claude Code
错误地把本地模型当作 200K 上下文。应按服务端实际 `N_CTX` 覆盖：

```bash
CLAUDE_CODE_MAX_CONTEXT_TOKENS=65536 \
  ./scripts/claude/claude-local.sh --backend llama-cpp --model <model>
```

本地模型 ID 可能触发 `[claude-code:unrecognized_model]` 诊断；只要后端正常
返回内容，该诊断不会阻止运行。

## llama.cpp

```bash
./scripts/llama-cpp/claude-server.sh <model>
./scripts/claude/claude-local.sh --backend llama-cpp --model <model>
```

该启动脚本启用 `--jinja`、设置稳定模型别名，并只分配一个并行 slot。旧版
llama.cpp 如果没有 `/v1/messages`，必须重新构建当前版本。

等价的环境变量：

```bash
ANTHROPIC_BASE_URL=http://127.0.0.1:8080 \
ANTHROPIC_AUTH_TOKEN=local \
ANTHROPIC_MODEL=<model> \
claude --model <model>
```

## vLLM 与 Strata

```bash
./scripts/vllm/serve.sh Qwen/Qwen3.5-4B
STRATA_FAMILY=qwen STRATA_MODEL=q2_0 ./scripts/strata/serve.sh
```

详细说明：

- [`usage-vllm.zh-CN.md`](usage-vllm.zh-CN.md)
- [`usage-strata.zh-CN.md`](usage-strata.zh-CN.md)

## Ollama 兼容代理

```bash
./scripts/ollama/serve.sh
sudo systemctl start litellm-proxy
./scripts/claude/claude-local.sh --backend ollama --model qwen2.5-coder:3b
```

## 故障排查

| 问题 | 处理方法 |
|---|---|
| 连接被拒绝 | 用 `--check` 确认地址、端口和服务器状态 |
| llama.cpp 不支持 `/v1/messages` | 更新并重新构建 llama.cpp |
| 工具调用失败 | 换用支持工具调用的 coder 模型，并保留 `--jinja` |
| vLLM 工具调用失败 | 设置正确的 `VLLM_TOOL_CALL_PARSER` |
| 显存不足 | 缩短上下文、停止其他后端，或使用更小量化模型 |
| Ollama thinking 错误 | 使用 `--backend ollama`，让代理移除 Anthropic thinking 参数 |
