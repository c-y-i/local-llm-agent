# 维护

[English](maintenance.md) | 简体中文

本文档记录模型添加、删除、检查与更新的常用命令。

## 导入 GGUF 到 Ollama

将 GGUF 文件放入 `models/` 后：

```bash
./scripts/ollama/import-to-ollama.sh <name> <name>:latest
```

## 检查软链接

```bash
./scripts/ollama/check-symlinks.sh
```

该脚本会报告：

- blob 数量
- 目标文件大小
- 悬空软链接
- 每个模型的摘要信息

## 删除模型

```bash
./scripts/ollama/remove-model.sh <model-tag>
```

## Ollama 端口排查

检查 `11434` 端口被谁占用：

```bash
ss -H -tlnp '( sport = :11434 )'
pgrep -af 'ollama serve'
```

如需重启手动启动的服务：

```bash
pkill -f "ollama serve"
./scripts/ollama/serve.sh
```

## 便携部署

便携部署请优先使用：

```bash
portable-ollama serve
```

完整说明见 [`portable-llm-launcher.zh-CN.md`](portable-llm-launcher.zh-CN.md)。
