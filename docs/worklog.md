# Worklog

This file is reserved for project-level release notes and reusable setup changes.

Machine-specific migration notes, local paths, one-off command history, and hardware snapshots should live in ignored local notes such as `.local/worklog.md`.

## Current Portable Baseline

- Project name: `local-llm-agent`.
- Default layout: this repo next to `llama-cpp/` and `Ollama/`.
- Public scripts resolve paths from `LOCAL_LLM_AGENT_ROOT`, `LLAMA_CPP_ROOT`, `OLLAMA_ROOT`, `OLLAMA_MODELS`, and `LLM_MODELS_DIR`.
- Cline service installation is generated from `systemd/llama-cline.service.in`.
- Large model files are ignored by default.
