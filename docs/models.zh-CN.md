# 模型

[English](models.md) | 简体中文

本文档是模型系列及用途目录，不直接涉及硬件选型。硬件建议见 [`hardware-matching.zh-CN.md`](hardware-matching.zh-CN.md)。

## 常见用途

| 模型系列 | 适用场景 | 备注 |
|---|---|---|
| Qwen Coder | 代码、工具调用、agent 工作流 | 本仓库优先推荐 |
| Qwen 通用系列 | 通用聊天、摘要、轻量推理 | 表现取决于模型大小和量化方式 |
| Llama 3.x | 通用聊天和备选方案 | 工具调用能力因模型而异 |
| Phi / Gemma 小模型 | 低配机器、快速响应 | 适合纯 CPU / SBC 或低显存场景 |

## Claude Code

Claude Code 对工具调用和响应格式要求较高。推荐从以下模型开始尝试：

- `qwen2.5-coder:3b`
- `qwen2.5-coder:7b`
- `llama3.2:3b`
- `phi4-mini:latest`

使用方式见 [`claude-code.zh-CN.md`](claude-code.zh-CN.md)。

## Cline

Cline 和其他 agent loop 需要模型能稳定输出符合格式要求的工具调用。如果模型持续输出错误的 XML 或 JSON tool call，请参考 `.clinerules` 和 [`cline.zh-CN.md`](cline.zh-CN.md)，或换用更适合代码和工具调用的模型。

## 维护原则

变更本地模型集合后，请更新本文档说明每个模型的用途。硬件相关建议放在 [`hardware-matching.zh-CN.md`](hardware-matching.zh-CN.md)。不要提交模型权重文件。
