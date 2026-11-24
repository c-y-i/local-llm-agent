# Agent Setup Instructions

When a user asks you to install, configure, or troubleshoot a complete local
coding-agent setup, follow [`docs/agent-setup.md`](docs/agent-setup.md).

Required behavior:

1. Inspect the operating system, CPU, RAM, GPU/VRAM, free disk space, existing
   commands, and current model inventory before recommending software.
2. Ask the user which model qualities matter most and which agent CLI they
   intend to use. Present compatible Qwen, Gemma, and other options with their
   size and tradeoffs.
3. Never download a model merely because it appears in a README example, test,
   or benchmark table. Examples are suggestions, not defaults.
4. Install only the backend, model, and agent CLI the user explicitly chooses.
5. Preserve existing model files and storage. Do not format, repartition, or
   bulk-move an unknown disk.
6. Verify prerequisites, model checksums, backend health, and one end-to-end
   agent request before declaring setup complete.

If the user cannot answer the model-choice questions, stop after reporting the
hardware assessment and recommended options. Do not silently choose a model.
