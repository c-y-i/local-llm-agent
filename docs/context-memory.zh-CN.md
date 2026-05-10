# Context 与 Memory

[English](context-memory.md) | 简体中文

本文档说明本地 agent 工作流中几类容易混淆的“记忆”概念。

## 类型

| 类型 | 作用 | 生命周期 |
|---|---|---|
| Prompt 上下文 | 当前请求可见的输入、系统提示、工具说明 | 单次请求或会话 |
| KV cache | 模型推理时复用已计算的 token | 服务运行期间 |
| Prompt cache | 某些运行时的 prompt 复用机制 | 取决于具体运行时 |
| 项目记忆 | `.clinerules`、文档、README 等持久化文件 | Git / 文件系统 |

## 上下文窗口

上下文窗口越大，能容纳的历史越多，但 KV cache 占用也会越高。显存不足时应该优先降低：

```bash
N_CTX=8192 ./scripts/llama-cpp/cline-server.sh <model>
```

或减少 GPU offload 层数：

```bash
N_GPU_LAYERS=16 ./scripts/llama-cpp/cline-server.sh <model>
```

## 项目记忆

建议把长期规则、架构说明和操作流程写入仓库文件，而不是依赖模型的会话记忆：

- `.clinerules`
- `README.md`
- `docs/*.md`
- 项目内设计文档

硬件对应的模型建议见 [`hardware-matching.zh-CN.md`](hardware-matching.zh-CN.md)。
