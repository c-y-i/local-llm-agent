# Copilot With Ollama

This repo is not only for Cline. A good default split is:

- Cline -> llama.cpp when you want tight control over GGUF files and context.
- Copilot Chat or Copilot CLI -> Ollama when you want local models inside the Copilot workflow.

## VS Code Copilot Chat

Ollama documents native VS Code integration through the Copilot Chat model picker. Current prerequisites are Ollama `0.18.3+`, VS Code `1.113+`, and GitHub Copilot Chat `0.41.0+`. VS Code may still ask you to sign in for model selection, even when using local models.

Start Ollama and add a model:

```bash
./scripts/ollama/serve.sh
ollama pull qwen2.5-coder:7b
ollama launch vscode
```

Then open Copilot Chat in VS Code and select a local Ollama model from the model picker. Make sure the model is marked local if VS Code shows both local and cloud choices.

![VS Code Language Models picker showing Ollama models](../media/copilot_ollama.png)

Manual setup in VS Code:

1. Open Copilot Chat.
2. Open the Language Models window from the settings/model picker UI.
3. Add Ollama as a provider.
4. Unhide the Ollama models you want to use.

## Copilot CLI

Ollama also supports Copilot CLI:

```bash
ollama launch copilot
```

To choose a model directly:

```bash
ollama launch copilot --model qwen2.5-coder:7b
```

For manual environment-variable setup:

```bash
export COPILOT_PROVIDER_BASE_URL=http://localhost:11434/v1
export COPILOT_PROVIDER_API_KEY=
export COPILOT_PROVIDER_WIRE_API=responses
export COPILOT_MODEL=qwen2.5-coder:7b
copilot
```

Copilot CLI expects strong tool support and a large context window. If a small local model fails tool calls, use it for chat/small edits, or switch to a larger coding model.

## Notes

- Copilot BYOK/local models apply to VS Code Chat features, not necessarily inline code completions.
- Organization policies may control whether BYOK or custom model providers are available.
- Local Ollama keeps inference local, but VS Code/Copilot sign-in and extension behavior still follow the tools' own policies.
- For Cline-specific tool-call guardrails, use [`cline.md`](cline.md).

## References

- Ollama VS Code integration: <https://docs.ollama.com/integrations/vscode>
- Ollama Copilot CLI integration: <https://docs.ollama.com/integrations/copilot-cli>
- GitHub Copilot CLI BYOK docs: <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-byok-models>
- GitHub BYOK changelog: <https://github.blog/changelog/2026-04-22-bring-your-own-language-model-key-in-vscode-now-available/>
