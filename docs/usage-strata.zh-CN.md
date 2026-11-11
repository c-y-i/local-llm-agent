# 使用 Strata

[English](usage-strata.md) | 简体中文

Strata 是面向超大型 Mixture-of-Experts 模型的专用推理引擎。它会把专家权重
分布到显存、系统内存和 SSD，而不是让小型模型变得更快。

请先从上游安装 Strata：

<https://github.com/Niko1221/Strata>

## 先检查计划

```bash
strata launch --family qwen --model q2_0 --plan
```

Strata 模型包可能达到数十或数百 GB。下载前必须确认内存、显存和磁盘是否足够。

## 通过本仓库启动

```bash
STRATA_FAMILY=qwen STRATA_MODEL=q2_0 ./scripts/strata/serve.sh
STRATA_FAMILY=qwen36 STRATA_MODEL=UD-Q4_K_XL ./scripts/strata/serve.sh
```

默认监听 `127.0.0.1:8082`，避免与 llama.cpp 的 `8080` 端口冲突。

设置 `STRATA_API_KEY` 可启用认证；未设置时脚本使用 `--no-api-key`，并假定
服务只监听本机。

模型包会下载到 `STRATA_MODELS_DIR`，默认是 `~/LLM/models/strata`。

## Claude Code

```bash
./scripts/claude/claude-local.sh --backend strata --model strata
```

如果 `/v1/models` 返回其他模型 ID，请使用返回的 ID。

Strata 最小的 Qwen3.8 模型包约需 27.6 GB 显存与内存总和；Qwen3.6 4-bit
计划约需 32 GB 系统内存。低内存模式会从 SSD 流式读取专家，速度会明显下降。
