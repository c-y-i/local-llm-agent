# Agent Setup Runbook

English | [简体中文](agent-setup.zh-CN.md)

This runbook is for a coding agent asked to turn a user's computer into a
working local-agent environment. The goal is a verified setup tailored to the
user's hardware and preferences, not a copy of the benchmark machine.

## Setup Contract

- Inspect before installing.
- Ask before downloading model weights.
- Treat Qwen, Gemma, DeepSeek, and other names in this repository as
  suggestions, not defaults.
- Install only the backend, model, and agent CLI the user chooses.
- Preserve existing disks, files, credentials, and agent configuration.
- Finish with an end-to-end test and a concise report.

Do not run the example download in the README until the user has selected a
model category and approved the proposed file size.

## 1. Inspect The Machine

Collect:

- operating system and architecture;
- CPU model and physical/logical core count;
- installed RAM;
- GPU model, VRAM, and driver version;
- free space on the intended model volume;
- Python, Git, CMake, CUDA, and NVIDIA driver availability;
- existing `llm`, `codex`, `claude`, `hermes`, and `ollama` commands;
- installed models and any partial `.part` downloads.

Useful commands:

```text
llm doctor
llm paths
llm models
```

```powershell
Get-CimInstance Win32_Processor
Get-CimInstance Win32_ComputerSystem
nvidia-smi
Get-PSDrive -PSProvider FileSystem
```

```bash
lscpu
free -h
nvidia-smi
df -h
```

If a command is unavailable, record that as unknown instead of guessing.

## 2. Classify The Hardware

Use the GPU/VRAM first when a supported accelerator is present. Use system RAM
for CPU-only inference. The selected file must leave room for the KV cache,
compute buffers, the operating system, and other applications.

| Available memory | Starting point | Notes |
|---|---|---|
| CPU only, 8 GB RAM or less | Qwen3.5-2B Q4 | Use short contexts and a lean agent toolset |
| 6-8 GB VRAM | Qwen3.5-2B or Qwen3.5-4B Q4 | Prefer 2B for long context or low latency |
| 10-12 GB VRAM | Qwen3.5-4B Q4 | Balanced default; Gemma is an alternative for general work |
| 14-16 GB VRAM | Qwen3.5-4B/9B; Gemma E4B | Larger options depend on RAM and context |
| 24 GB VRAM or more | 9B-14B options | Use the largest model that passes the smoke test |

These are starting points, not hard compatibility claims. Model architecture,
context length, KV-cache type, offload, and the selected agent all affect
whether a model fits.

## 3. Ask The User

Before recommending a download, ask a compact question such as:

> What should the local model optimize for: balanced coding, fastest
> response/lowest memory, general assistant work, maximum quality, or no model
> yet? Which agent CLI do you intend to use: Codex, Claude Code, or Hermes?

Provide a small set of compatible suggestions with size and tradeoffs:

- **Balanced coding:** Qwen3.5-4B Q4_K_M.
- **Fast or low-memory:** Qwen3.5-2B Q4_K_M.
- **General assistant:** Gemma 4 E4B QAT, when the hardware has enough room.
- **Higher quality:** Qwen3.5-9B or the tested 14B options, with context and
  RAM tradeoffs stated explicitly.

Do not label a model "recommended" without tying it to the user's answer.
Do not start a multi-gigabyte download while waiting for the answer.

In a non-interactive environment, stop after presenting the assessment and
options. A missing answer is not permission to install.

## 4. Confirm The Proposal

For each proposed model, report:

- exact model ID and quant;
- source repository and expected license;
- download size;
- expected runtime backend;
- approximate memory/context implications;
- checksum, when the publisher provides one;
- why it fits the user's stated goal.

Ask the user to choose one model or explicitly defer model installation.

## 5. Install The Backend

llama.cpp is the primary tested backend. Install an agent CLI separately.

On Windows, prefer the repository's documented prebuilt CUDA path when a CUDA
compiler is unavailable. A missing `nvcc` does not prevent use of a prebuilt
CUDA runtime.

Detect existing agent CLIs before installing anything:

```text
codex --version
claude --version
hermes --version
```

Ask which agent the user wants. Do not install all three by default.

## 6. Install Only The Selected Model

Resolve the model directory first:

```text
llm paths
```

Download to a `.part` file, resume interrupted transfers, and rename only after
the complete size and SHA-256 match the publisher's metadata. Record the
source and checksum in the final report.

Never:

- format a model disk;
- overwrite a complete model with a partial file;
- remove a user's existing models without approval;
- place weights inside the Git repository.

## 7. Verify End To End

Run:

```text
llm doctor
llm models
llm start
```

Then verify:

1. the backend becomes healthy;
2. `/v1/models` reports the selected model;
3. one short chat request succeeds;
4. the selected agent launches through its local wrapper;
5. control tokens such as `<think>` do not leak into user-visible text;
6. the working directory is preserved when launching the agent.

Stop servers started only for testing unless the user asked to keep them
running.

## 8. Report The Result

Report:

- detected hardware;
- selected backend and agent CLI;
- selected model, size, storage path, and checksum status;
- context choice and GPU/CPU split;
- verification commands and results;
- known limitations or optional components not installed.

Avoid saying "ready" until the end-to-end test passes.

## Recovery And Safety

If a removable Linux filesystem disappears, stop writing to it and preserve
the disk. Do not format it to regain access from Windows. Prefer a read-only
filesystem inspection first, then use the filesystem's native repair tools
when necessary.
