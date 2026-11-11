# 后端与存储

[English](backends.md) | 简体中文

## 当前范围

llama.cpp 是主要后端，Ollama 是辅助后端和共享模型存储。vLLM 与 Strata
暂时不在当前范围内。

## 前置条件

- Python 3 和 `venv`
- Git
- curl
- CMake、Make 和 C/C++ 编译器
- 对应 Agent 的 CLI：Claude Code、Codex CLI 或 Hermes
- 使用 NVIDIA 加速时需要驱动和可用的 CUDA 构建

```bash
./scripts/setup/check-prereqs.sh
llm doctor
```

## 存储

```text
~/LLM/
  models/        # 标准 GGUF
  llama.cpp/     # 源码和构建
  ollama/        # Ollama 状态和模型链接
  .venv/         # Python 环境
  run/           # 日志和 PID
  codex-local/   # 隔离的 Codex 状态
  hermes-local/  # 隔离的 Hermes 状态
```

可在 `.env` 中修改 `LLM_ROOT` 或单独路径。模型、构建、缓存、虚拟环境和
凭据都不能进入 Git 仓库。

## llama.cpp

```bash
source .venv/bin/activate
llm build llama-cpp
llm build llama-cpp --cuda OFF
llm start llama-cpp qwen3.5-4b-official-Q4_K_M
```

需要时，`hermes-local`、`codex-local` 和 `claude-local` 会后台启动首选 GGUF。
默认地址为 `http://127.0.0.1:8080`。

## 添加 GGUF

将 `*.gguf` 放入 `$LLM_MODELS_DIR`，去掉 `.gguf` 后缀就是模型 ID：

```text
~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf
```

从 Hugging Face 下载示例：

```bash
curl -fL --retry 5 -C - \
  -o ~/LLM/models/qwen3.5-2b-official-Q4_K_M.gguf.part \
  https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/main/Qwen3.5-2B-Q4_K_M.gguf
mv ~/LLM/models/qwen3.5-2b-official-Q4_K_M.gguf.part \
  ~/LLM/models/qwen3.5-2b-official-Q4_K_M.gguf
```

使用前应核对 Hugging Face 页面提供的 SHA-256。

## Ollama

```bash
llm install ollama
./scripts/setup/configure-ollama.sh
llm start ollama qwen3.5-4b-official:latest
```

Ollama 可通过 `scripts/ollama/` 下的辅助脚本与 llama.cpp 共享同一份 GGUF，
不要保留重复的 GB 级文件。

## 生命周期和日志

同一个 8080 端口一次只能运行一个 llama.cpp 服务。后台启动时 PID 位于
`$LLM_ROOT/run/llama-server.pid`，日志位于
`$LLM_ROOT/run/llama-server.log`。

Ollama 作为独立守护进程管理。需要由 `llm start ollama` 启动时，PID 写入
`$LLM_ROOT/run/ollama.pid`，日志追加到 `$LLM_ROOT/run/ollama.log`。

```bash
llm status
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8080/props
curl -s http://127.0.0.1:8080/metrics
curl -s http://127.0.0.1:11434/api/ps
llm logs --backend llama-cpp
llm logs --backend ollama --follow
```
