# 硬件与模型匹配

[English](hardware-matching.md) | 简体中文

本文档用于根据目标机器选择首批模型。模型文件和量化方式更新很快，建议以这里为起点，再根据实际显存、内存和响应速度灵活调整。

## 快速建议

| 硬件 | 推荐起点 | 说明 |
|---|---|---|
| 纯 CPU / SBC | `qwen3:1.7b`、`llama3.2:3b` | 优先保证能跑起来，响应稳定 |
| 普通笔记本 / 小显存 GPU | `qwen3:4b`、`qwen2.5-coder:3b` | 适合日常聊天和轻量代码任务 |
| 8-12 GB 显存 | 7B-14B 量化模型 | 可尝试更强的 coder 或通用模型 |
| 16-24 GB 显存 | 14B-32B 量化模型 | 更适合 agent 和长上下文场景 |
| 多 GPU / 高端工作站 | 32B-70B 量化模型 | 需要额外配置服务参数并测试显存占用 |

## 选型原则

- 先用小模型确认启动器、端口、模型目录和工具链都能正常工作。
- Cline / Claude Code 这类 agent 工作流，优先选择工具调用能力稳定的 coder 模型。
- 上下文越长，KV cache 占用越高；不要只看模型文件大小。
- 纯 CPU 机器可以跑小模型，但 agent 工具调用会明显偏慢。

## 与其他文档的关系

- 模型系列说明见 [`models.zh-CN.md`](models.zh-CN.md)。
- 上下文与 KV cache 说明见 [`context-memory.zh-CN.md`](context-memory.zh-CN.md)。
- Ollama 使用说明见 [`usage-ollama.zh-CN.md`](usage-ollama.zh-CN.md)。
