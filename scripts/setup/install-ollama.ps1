$ErrorActionPreference = "Stop"

if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host "Ollama is already installed: $((Get-Command ollama).Source)"
    exit 0
}

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "Install Ollama from https://ollama.com/download/windows, then rerun this script."
}

& winget install --id Ollama.Ollama -e --accept-package-agreements --accept-source-agreements
if ($LASTEXITCODE -ne 0) {
    throw "Ollama installation failed. Install it from https://ollama.com/download/windows."
}

Write-Host "Ollama installed. Open a new terminal, then run: llm doctor"
