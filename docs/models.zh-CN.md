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

## 从 Hugging Face 拉取模型

Hugging Face 上的任意 GGUF 模型均可通过 `hf.co/` 前缀直接用 Ollama 拉取和运行，无需单独下载或转换：

```bash
# 格式
ollama pull hf.co/<用户>/<仓库>:<量化标签>
ollama run  hf.co/<用户>/<仓库>:<量化标签>

# 示例
ollama pull hf.co/bartowski/Qwen2.5-14B-Instruct-GGUF:Q4_K_M
ollama run  hf.co/bartowski/Qwen2.5-14B-Instruct-GGUF:Q4_K_M
```

量化标签对应文件名去掉模型名前缀和 `.gguf` 后缀，例如 `Qwen2.5-14B-Instruct-Q4_K_M.gguf` → `:Q4_K_M`。

**推荐量化方式：**

| 标签 | 大小与质量 |
|---|---|
| `Q4_K_M` | 大小与质量最佳平衡，首选。 |
| `Q5_K_M` | 质量更高，显存占用更多，显存充裕时推荐。 |
| `IQ4_XS` | 比 Q4_K_M 略小，质量相近。 |
| `Q2_K` | 体积最小，质量最低，仅在内存极度受限时使用。 |

可在 [huggingface.co/bartowski](https://huggingface.co/bartowski) 浏览模型——该账号为主流模型系列提供了可靠的 GGUF 量化版本。

## 无限制模型（Uncensored）

这些模型的安全微调已被移除或大幅削减，对大多数话题不会拒绝回答。**没有** `tools` 能力，无法用于 Cline agent 工作流，仅适合自由聊天。

| 模型 | Ollama 标签 | 大小 | 显存占用 | 说明 |
|---|---|---|---|---|
| dolphin-phi 2.7B | `dolphin-phi:2.7b` | 1.6 GB | 完全在 GPU | 基于 Phi-2 的 Dolphin 微调，速度快，体积小。 |
| dolphin-llama3 8B | `dolphin-llama3:8b` | 4.7 GB | CPU 溢出 | 基于 Llama 3 8B 的 Dolphin 2.9 微调，效果更强，GTX 1050 Ti 上约 6–10 tok/s。 |

```bash
ollama pull dolphin-phi:2.7b
ollama pull dolphin-llama3:8b
```

## 维护原则

变更本地模型集合后，请更新本文档说明每个模型的用途。硬件相关建议放在 [`hardware-matching.zh-CN.md`](hardware-matching.zh-CN.md)。不要提交模型权重文件。
