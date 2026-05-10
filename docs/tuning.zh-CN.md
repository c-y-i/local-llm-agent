# 参数调优

[English](tuning.md) | 简体中文

本文档记录本地模型调参与 Modelfile 工作流的基本原则。

## 常用参数

| 参数 | 作用 |
|---|---|
| `temperature` | 控制输出随机性，越低越稳定 |
| `top_p` | 核采样范围 |
| `num_ctx` / `N_CTX` | 上下文长度 |
| `num_predict` | 最大生成 token 数 |
| `repeat_penalty` | 重复惩罚 |

Agent 工作流通常建议使用较低的 `temperature`，以减少输出格式漂移。

## llama.cpp

通过环境变量调整：

```bash
N_CTX=8192 N_GPU_LAYERS=32 ./scripts/llama-cpp/cline-server.sh <model>
```

## Ollama Modelfile

Modelfile 放在 `modelfiles/` 目录中，适合保存模型模板和参数配置。

创建或更新模型：

```bash
ollama create <tag> -f modelfiles/<file>
```

## Cline 注意事项

Cline 会在用户 prompt 前面加上较大的系统提示和工具说明。不要假设所有模型都能使用相同的上下文长度。请以 `cline-server.sh` 启动时打印的 context 值为准。

相关文档：

- [`context-memory.zh-CN.md`](context-memory.zh-CN.md)
- [`cline.zh-CN.md`](cline.zh-CN.md)
