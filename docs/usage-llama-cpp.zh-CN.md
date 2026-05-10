# llama.cpp 用法

[English](usage-llama-cpp.md) | 简体中文

以下命令使用 `scripts/common/env.sh` 中定义的默认路径。

## 列出模型

```bash
./scripts/llama-cpp/llm-list.sh
```

## 直接运行模型

```bash
./scripts/llama-cpp/llm-run.sh <model-name>
```

示例：

```bash
./scripts/llama-cpp/llm-run.sh qwen2.5-coder-3b
```

## 启动 OpenAI 兼容服务

```bash
./scripts/llama-cpp/llm-serve.sh <model-name> [port]
```

示例：

```bash
./scripts/llama-cpp/llm-serve.sh qwen2.5-coder-3b 8080
```

服务端点：

- `http://127.0.0.1:<port>/v1/chat/completions`
- `http://127.0.0.1:<port>/v1/completions`
- `http://127.0.0.1:<port>/v1/models`

## Cline 服务

推荐的 Cline 接入方式：

```bash
./scripts/llama-cpp/cline-server.sh
```

也可以指定模型和端口：

```bash
./scripts/llama-cpp/cline-server.sh qwen2.5-coder-3b 8081
```

Cline 配置：

| 字段 | 值 |
|---|---|
| API Provider | `OpenAI Compatible` |
| Base URL | `http://127.0.0.1:8080/v1` |
| API Key | 任意值即可 |
| Model ID / Context | 启动脚本会打印 |

完整 Cline 指南见 [`cline.zh-CN.md`](cline.zh-CN.md)。

## 环境变量

| 变量 | 说明 |
|---|---|
| `LLAMA_CPP_ROOT` | llama.cpp 源码与构建目录 |
| `LLAMA_CPP_BIN` | `llama-cli` 路径 |
| `LLAMA_SERVER_BIN` | `llama-server` 路径 |
| `N_GPU_LAYERS` | GPU offload 层数 |
| `N_CTX` | 上下文长度 |
| `HOST` | 监听地址，默认 `127.0.0.1` |
