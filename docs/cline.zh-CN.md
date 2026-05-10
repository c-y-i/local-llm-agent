# Cline

[English](cline.md) | 简体中文

推荐路径：Cline -> OpenAI 兼容 provider -> 本地 llama.cpp server。这样可以精细控制 GGUF 文件、上下文长度和 GPU offload。

## 启动服务

```bash
./scripts/llama-cpp/cline-server.sh
```

指定模型：

```bash
./scripts/llama-cpp/cline-server.sh qwen2.5-coder-3b
```

指定端口：

```bash
./scripts/llama-cpp/cline-server.sh qwen2.5-coder-3b 8081
```

## Cline 配置

| 字段 | 值 |
|---|---|
| API Provider | `OpenAI Compatible` |
| Base URL | `http://127.0.0.1:8080/v1` |
| API Key | `114514` |
| Model ID | 启动脚本打印的模型名 |
| Context | 启动脚本打印的上下文长度 |

![Cline running with a local Ollama model](../media/cline_demo.png)

## 也可以直接连接 Ollama

```bash
./scripts/ollama/serve.sh
```

Cline 中配置：

| 字段 | 值 |
|---|---|
| API Provider | `Ollama` |
| Base URL | `http://127.0.0.1:11434` |

## 常见问题

| 问题 | 处理方法 |
|---|---|
| `Connection refused` | 确认 `cline-server.sh` 或服务正在运行，并检查端口 |
| 工具调用输出格式错误 | 换用更适合工具调用的 coder 模型，或参考 `.clinerules` |
| 上下文不够 | 缩小任务范围，或用更大的上下文启动服务 |
| 显存不足 | 降低 `N_CTX` 或 `N_GPU_LAYERS`，或换用更小的模型 |

## 相关文档

- llama.cpp 命令见 [`usage-llama-cpp.zh-CN.md`](usage-llama-cpp.zh-CN.md)。
- 模型选择见 [`models.zh-CN.md`](models.zh-CN.md) 和 [`hardware-matching.zh-CN.md`](hardware-matching.zh-CN.md)。
