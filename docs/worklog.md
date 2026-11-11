# Worklog

This file is reserved for project-level release notes and reusable setup changes.

Machine-specific migration notes, local paths, one-off command history, and hardware snapshots should live in ignored local notes such as `.local/worklog.md`.

## Current Portable Baseline

- Project name: `local-llm-agent`.
- Default layout: lightweight repo with heavy state under `LLM_ROOT` (`~/LLM` by default).
- `llm` exposes path inspection, diagnostics, model discovery, engine installation/build, serving, and Claude Code launch.
- Bare `llm` opens an interactive menu; `llm start` selects a backend/model and `llm agent` selects an agent for the running model.
- Agent compatibility covers Claude Code, Codex CLI Responses providers, and Hermes custom OpenAI-compatible endpoints.
- Public scripts resolve paths from `LLM_ROOT`, `LLAMA_CPP_ROOT`, `OLLAMA_ROOT`, `OLLAMA_MODELS`, `LLM_MODELS_DIR`, `HF_HOME`, and Strata path variables.
- Backend defaults resolve llama.cpp, vLLM, and Strata URLs through `scripts/common/env.sh`.
- Claude Code can connect natively to current llama.cpp, vLLM, and Strata servers through the shared launcher; Ollama retains the compatibility proxy.
- Cline service installation is generated from `systemd/llama-cline.service.in`.
- Large model files are ignored by default.
