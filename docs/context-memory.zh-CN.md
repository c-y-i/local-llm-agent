# 上下文与内存

[English](context-memory.md) | 简体中文

## 唯一来源

运行中的后端决定上下文窗口。Agent 启动器读取服务端实际值，不应保留会静默覆盖
服务端的客户端固定值。

llama.cpp：

```bash
curl -s http://127.0.0.1:8080/props
curl -s http://127.0.0.1:8080/v1/models
```

两者都会报告实际分配的 `n_ctx`。模型训练上限可能大于或等于当前窗口。

## 上下文、KV Cache 和文件

| 项目 | 持久化 | 用途 |
|---|---|---|
| 上下文窗口 | 否 | 单次请求可考虑的最大 token 数 |
| KV cache | 否 | 运行时注意力状态，通常位于显存或内存 |
| 会话历史 | 取决于 Agent | 对话记录 |
| 仓库文件 | 是 | 代码、说明和文档 |
| Agent 指令 | 是 | `AGENTS.md`、Hermes `SOUL.md` 等 |

文件不会自动成为永久记忆，Agent 必须在任务中搜索或读取它们。

## 上下文大小

- 16K-32K：保守、快速，适合小修改。
- 64K：Qwen3.5-4B 编码工作的实用默认值。
- 128K：适合较大仓库或长会话。
- 256K：当前硬件上的实验值，预填充更慢且内存压力高。

Qwen3.5-2B 原生上限是 262,144 token。已验证 128K（KV 在 GPU）和
256K（`KV_OFFLOAD=0`）。

## llama.cpp 控制

```bash
llm start llama-cpp qwen3.5-4b-official-Q4_K_M --context 65536
llm start llama-cpp qwen3.5-4b-official-Q4_K_M --gpu-layers 24
KV_CACHE_TYPE=q8_0 llm start llama-cpp qwen3.5-4b-official-Q4_K_M
KV_CACHE_TYPE=q4_0 KV_OFFLOAD=0 \
  llm start llama-cpp qwen3.5-2b-official-Q4_K_M --context 262144
```

降低 GPU 层数会把模型层移到 CPU/RAM；关闭 KV offload 会把缓存移到 CPU/RAM。

## Hermes 上下文

如果目标是跟随活动后端，不要在 Hermes 中保留全局
`model.context_length` 或 `model.ollama_num_ctx`。启动器会检测冲突并提示删除。

Agent 指令文件也会消耗上下文，应保持简短，并按需加载详细流程。

## 调试

```bash
llm status
curl -s http://127.0.0.1:8080/props
curl -s http://127.0.0.1:8080/slots
curl -s http://127.0.0.1:8080/metrics
ollama ps
nvidia-smi
```
