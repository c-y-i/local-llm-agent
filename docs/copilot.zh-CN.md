# Copilot

[English](copilot.md) | 简体中文

VS Code Copilot Chat 可以通过 Ollama 使用本地模型。实际体验取决于 VS Code、Copilot Chat 扩展和 Ollama 的版本。

## VS Code Copilot Chat

启动 Ollama：

```bash
./scripts/ollama/serve.sh
```

准备模型：

```bash
ollama pull qwen2.5-coder:7b
```

然后在 VS Code Copilot Chat 的模型选择器中选择本地 Ollama 模型即可。

![VS Code Language Models picker showing Ollama models](../media/copilot_ollama.png)

## Copilot CLI

示例环境变量：

```bash
export COPILOT_PROVIDER_BASE_URL=http://localhost:11434/v1
export COPILOT_PROVIDER_API_KEY=
export COPILOT_PROVIDER_WIRE_API=responses
export COPILOT_MODEL=qwen2.5-coder:7b
```

## 注意事项

- Copilot CLI 对工具调用和上下文要求较高。
- 小模型可以胜任聊天和简单修改，但不一定适合复杂 agent 工作流。
- Cline 的工具调用注意事项见 [`cline.zh-CN.md`](cline.zh-CN.md)。
