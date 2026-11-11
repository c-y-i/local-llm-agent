# 模型

[English](models.md) | 简体中文

## 已验证模型

下列模型只是用于验证 6 GB 参考笔记本的示例，不是强制目录、唯一选择或性能
上限。显存和内存更大的机器可以运行更大、更强的 GGUF 模型。

| 模型 | 本地文件 | 大小 | 用途 |
|---|---|---:|---|
| Qwen3.5-4B 官方 Q4_K_M | `qwen3.5-4b-official-Q4_K_M.gguf` | 2.6 GB | 推荐的日常 Agent 编码模型 |
| Qwen3.5-2B 官方 Q4_K_M | `qwen3.5-2b-official-Q4_K_M.gguf` | 1.2 GB | 更快、更低内存，支持大上下文 |
| Gemma 4 E4B 官方 QAT Q4_0 | `gemma4-e4b-official-QAT-Q4_0.gguf` | 4.8 GB | 通用和多模态方向 |
| Qwen3.5-9B Defiant IQ3_M | `qwen3.5-9b-defiant-IQ3_M.gguf` | 5.2 GB | 实验性较大模型，CPU/RAM 压力更高 |
| Huihui Qwen3.5-2B abliterated | Ollama 标签 `huihui_ai/qwen3.5-abliterated:2b-agent` | 1.9 GB | Agent 就绪的无审查 Ollama 模型，32K 上下文 |
| Huihui Qwen3.5-2B abliterated F16 | `huihui-qwen3.5-2b-abliterated-f16.gguf` | 3.8 GB | llama.cpp 高精度 GGUF，默认保守 32K 上下文 |
| Huihui Qwen3.5-4B abliterated | Ollama 标签 `huihui_ai/qwen3.5-abliterated:4b-agent` | 3.3 GB | Agent 就绪的无审查 Ollama 模型，32K 上下文 |

在测试用 6 GB GPU 上，Qwen3.5-4B 是本地编码 Agent 的默认建议。
Qwen3.5-2B 适合更重视速度或上下文大小的场景。用户应根据自己的硬件档位和
质量需求选择模型，而不必局限于这些示例。

官方兼容 GGUF 下载：

```bash
curl -fL --retry 5 -C - \
  -o ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf.part \
  https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/main/Qwen3.5-4B-Q4_K_M.gguf
mv ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf.part \
  ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf
sha256sum ~/LLM/models/qwen3.5-4b-official-Q4_K_M.gguf
# 应为 00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4

curl -fL --retry 5 -C - \
  -o ~/LLM/models/qwen3.5-2b-official-Q4_K_M.gguf.part \
  https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/main/Qwen3.5-2B-Q4_K_M.gguf
mv ~/LLM/models/qwen3.5-2b-official-Q4_K_M.gguf.part \
  ~/LLM/models/qwen3.5-2b-official-Q4_K_M.gguf
sha256sum ~/LLM/models/qwen3.5-2b-official-Q4_K_M.gguf
# 应为 aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223
```

## Agent 适配

| 模型 | Claude Code | Codex CLI | Hermes |
|---|---|---|---|
| Qwen3.5-4B 官方 | 已验证 | 已验证 | 已验证 |
| Qwen3.5-2B 官方 | 支持 | 支持 | 已验证 |
| Gemma 4 E4B | 实验性 | 实验性 | 实验性 |
| Qwen3.5-9B Defiant | 实验性 | 实验性 | 实验性 |
| Huihui Qwen3.5-2B abliterated | 当前 llama.cpp 构建不支持 | 未测试 | 仅 Ollama，尚未进行 Agent 验证 |
| Huihui Qwen3.5-2B abliterated F16 | 已验证 llama.cpp 可加载 | 未测试 | 尚未进行 Agent 验证 |
| Huihui Qwen3.5-4B abliterated | 未安装 llama.cpp 版本 | 未测试 | 仅 Ollama，尚未进行 Agent 验证 |

验证结果代表协议兼容并成功完成本地请求，不代表小模型能可靠完成复杂多步修改。

### Huihui Abliterated 变体

该模型通过发布者的 Ollama 标签安装。其 GGUF 可被 Ollama 使用，但当前
llama.cpp 构建会因 `qwen35.rope.dimension_sections` 元数据而拒绝加载。
因此标准文件保存在 `~/LLM/ollama/models/external/`，而不是共享的
llama.cpp 模型目录。

通过 Ollama 使用 Agent 就绪标签：

```bash
llm start ollama huihui_ai/qwen3.5-abliterated:2b-agent
```

这是无审查实验模型，尚未验证 Agent 编码能力，请谨慎审查输出。

单独的 mradermacher F16 GGUF 已验证可由 llama.cpp 加载：

```bash
llm start llama-cpp huihui-qwen3.5-2b-abliterated-f16
```

F16 权重本身占用 3.8 GB，尚未计算 KV cache 和计算缓冲区，因此菜单默认上下文
保守设置为 32K。已验证选项为 16K、32K、64K、128K 和 256K。128K 的 KV
cache 可以放在 GPU；256K 会自动设置 `KV_OFFLOAD=0`，把 cache 移到系统内存。

## Ollama Agent 标签

导入的 Ollama 模型已使用明确的 renderer/parser、确定性采样和更大的上下文重建：

| 标签 | 上下文 | 工具 |
|---|---:|---|
| `qwen3.5-2b-official:latest` | 默认 64K，可选至 256K | 已验证 |
| `qwen3.5-4b-official:latest` | 默认 64K，可选至 128K | 配置已验证 |
| `huihui_ai/qwen3.5-abliterated:2b-agent` | 默认 32K，可选至 128K | 已验证 |
| `huihui_ai/qwen3.5-abliterated:4b-agent` | 默认 32K，可选至 64K | 配置已验证 |
| `gemma4-e4b-official:latest` | 默认 16K，可选至 64K | 配置已验证 |
| `qwen3.5-9b-defiant-uncensored:latest` | 默认 16K，可选至 64K | 配置已验证 |

原生 Ollama `/api/chat` 和 OpenAI 兼容 `/v1/chat/completions` 均已返回结构化工具调用。

## 上下文和内存

上下文容量取决于模型架构、KV heads、缓存类型、上下文长度以及 KV cache
是否在 GPU 上。

| 模型 | 默认上下文 | GPU 层数 |
|---|---:|---:|
| Qwen3.5-2B | 128K | 全部 |
| Qwen3.5-4B | 64K | 全部 |
| Qwen3.5-9B | 32K | 24 |
| Gemma 4 E4B | 32K | 30 |

这些只是启动默认值，不是 Agent 的固定限制。Agent 使用运行中服务端报告的实际值。

## 模型存储

GGUF 放在 `$LLM_MODELS_DIR`，仓库保持轻量。Ollama 应尽量链接同一份标准文件。

```bash
llm models
llm models --sort name
```

默认自动按大小从小到大排序。

## Hermes 提示开销

小模型的上下文中，Hermes 工具和系统指令占比明显。默认情况下，项目内容之前
约消耗 13K token。Skills 采用渐进式加载，预加载大型 skill 才会一次写入完整内容。

2B 编码会话：

```bash
hermes-local -t terminal,file,skills,todo,clarify
```

保留 `skills` 以便按需读取，不要无必要时预加载大型 skill。
