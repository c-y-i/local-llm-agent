# 使用 vLLM

[English](usage-vllm.md) | 简体中文

vLLM 提供 OpenAI 和 Anthropic 兼容接口，适合模型完全驻留在 GPU 上的高吞吐
推理。它加载 Hugging Face safetensors、AWQ 或 GPTQ 权重，不加载 GGUF。

## 安装

```bash
llm install vllm
source "$HOME/LLM/.venv/bin/activate"
python -m pip install --upgrade pip
```

vLLM 虚拟环境安装在 `LLM_VENV_DIR`，不会写入 Git 仓库。

## 启动

```bash
./scripts/vllm/serve.sh Qwen/Qwen3.5-4B
```

默认端口为 `8000`，默认模型 ID 为 `Qwen3.5-4B`。

常用环境变量：

| 变量 | 默认值 | 作用 |
|---|---|---|
| `VLLM_PORT` | `8000` | 服务端口 |
| `VLLM_HOST` | `127.0.0.1` | 监听地址 |
| `VLLM_SERVED_MODEL_NAME` | 模型目录名 | 客户端使用的稳定模型 ID |
| `VLLM_TOOL_CALL_PARSER` | `qwen3_coder` | 工具调用解析器 |
| `VLLM_MAX_MODEL_LEN` | 模型默认值 | 最大上下文长度 |
| `VLLM_EXTRA_ARGS` | 空 | 额外的 `vllm serve` 参数 |

Qwen3、Qwen3.5 和 Qwen3-Coder 通常使用 `qwen3_coder` 解析器。其他模型必须使用
vLLM 文档指定的解析器，否则 Claude Code 的工具调用可能无法工作。

## 接口

```text
OpenAI:    http://127.0.0.1:8000/v1
Anthropic: http://127.0.0.1:8000
Messages:  http://127.0.0.1:8000/v1/messages
```

## Claude Code

```bash
./scripts/claude/claude-local.sh --backend vllm --model Qwen3.5-4B
```

在 6 GB 显存上，应选择 4-bit 模型，并为 KV cache 留出空间。单用户笔记本推理
通常使用 llama.cpp 或 Ollama 更高效。
