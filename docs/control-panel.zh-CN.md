# 控制面板

[English](control-panel.md) | 简体中文

控制面板是单文件 Python 标准库实现的 Web UI，无需安装额外依赖。

## 启动

```bash
python3 control_panel.py
```

默认访问地址：

```text
http://localhost:8766
```

监控面板是只读状态页：

```bash
python3 monitor.py
```

默认访问地址：

```text
http://localhost:8765
```

<img src="../media/dashboard.gif" alt="Local LLM Control Panel dashboard" width="720">

## 功能

控制面板可查看：

- Ollama、llama-cline、litellm-proxy 服务状态
- Anthropic proxy `:4000` 和 Stable Diffusion WebUI `:7860` 端口探测
- GPU、系统、磁盘和模型目录状态
- 已安装和已加载的 Ollama 模型
- 服务 start / stop / restart
- Ollama stop / unload 操作

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `LLM_DASHBOARD_HOST` | `127.0.0.1` | 监听地址 |
| `LLM_DASHBOARD_PORT` | `8766` | 控制面板端口 |
| `MONITOR_PORT` | `8765` | 旧版监控端口变量 |

控制操作仅接受 localhost 连接，并以当前用户身份运行。
