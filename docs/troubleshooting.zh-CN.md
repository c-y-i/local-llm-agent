# 故障排查

[English](troubleshooting.md) | 简体中文

## 从这里开始

```bash
llm doctor
llm status
llm models
```

## `llm` 提示虚拟环境未激活

`llm` 仍然需要显式激活：

```bash
source /home/cy/Projects/local-llm-agent/.venv/bin/activate
```

`claude-local`、`codex-local` 和 `hermes-local` 会自动激活，可在任意目录运行。

## Ollama 显示 `ready` 但没有活动模型

Ollama 守护进程已运行，但没有加载模型，因此不是活动推理后端：

```bash
llm start ollama qwen3.5-4b-official:latest
```

也可以直接运行 Agent 命令，它会按需启动首选 llama.cpp 模型。

## Agent 启动了错误模型

切换前先停止当前服务，或显式启动目标模型：

```bash
llm start llama-cpp qwen3.5-2b-official-Q4_K_M
```

同一个 llama.cpp 8080 端口一次只能运行一个模型。

## Hermes 显示较小上下文

先检查服务端：

```bash
curl -s http://127.0.0.1:8080/props
```

删除冲突设置并重启 Hermes：

```bash
HERMES_HOME=/home/cy/LLM/hermes-local \
  hermes config unset model.context_length
HERMES_HOME=/home/cy/LLM/hermes-local \
  hermes config unset model.ollama_num_ctx
```

## CUDA 显存不足

CLI 正常会保证同一时间只运行一个引擎。如果仍有旧服务运行，请先停止它，再
降低上下文、GPU 层数，或把 KV cache 移到内存：

```bash
llm status
ollama ps
nvidia-smi
llm start llama-cpp MODEL --context 32768
llm start llama-cpp MODEL --gpu-layers 24
KV_OFFLOAD=0 llm start llama-cpp MODEL --context 65536
```

## 后台 llama.cpp 启动失败

```bash
tail -n 100 ~/LLM/run/llama-server.log
cat ~/LLM/run/llama-server.pid
ss -ltnp '( sport = :8080 )'
```

## 看不到 Ollama 日志

Ollama 在守护进程中运行，不是 Agent 命令的前台子进程。使用托管日志：

```bash
llm logs --backend ollama
llm logs --backend ollama --follow
```

如果 `$LLM_ROOT/run/ollama.log` 不存在，请通过 `llm start ollama` 启动
Ollama，它会创建带持久日志的托管守护进程。

## Agent 工具调用不稳定

- 复杂多步修改优先使用 Qwen3.5-4B。
- 小模型使用精简 Hermes 工具集。
- 不要预加载不必要的大型 skill。
- 保持仓库说明简短。
- 使用 Git 或可丢弃分支。

```bash
hermes-local -t terminal,file,skills,todo,clarify
```

## 运行时检查

```bash
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8080/props
curl -s http://127.0.0.1:8080/slots
curl -s http://127.0.0.1:8080/metrics
curl -s http://127.0.0.1:11434/api/ps
```
