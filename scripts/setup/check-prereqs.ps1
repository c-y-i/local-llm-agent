$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:LOCAL_LLM_AGENT_ROOT = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
. (Join-Path $env:LOCAL_LLM_AGENT_ROOT "scripts\common\env.ps1")

$missing = 0
function Check-Command {
    param([string]$Name, [switch]$Optional)
    $found = Get-Command $Name -ErrorAction SilentlyContinue
    if ($found) {
        Write-Host ("ok   {0,-16} {1}" -f $Name, $found.Source)
    } elseif ($Optional) {
        Write-Host ("opt  {0,-16} not found" -f $Name)
    } else {
        Write-Host ("miss {0,-16} not found" -f $Name)
        $script:missing++
    }
}

Write-Host "local-llm-agent paths"
foreach ($name in @(
    "LOCAL_LLM_AGENT_ROOT",
    "LLM_ROOT",
    "LLAMA_CPP_ROOT",
    "OLLAMA_ROOT",
    "LLM_MODELS_DIR",
    "OLLAMA_MODELS",
    "LLM_VENV_DIR",
    "LLAMA_CPP_BASE_URL",
    "OLLAMA_BASE_URL"
)) {
    Write-Host ("  {0}={1}" -f $name, [Environment]::GetEnvironmentVariable($name))
}

Write-Host ""
Write-Host "commands"
foreach ($name in @("python", "git", "cmake", "curl", "nvidia-smi", "nvcc")) {
    Check-Command $name
}
Check-Command "ollama" -Optional
Check-Command "codex" -Optional
Check-Command "claude" -Optional
Check-Command "hermes" -Optional

if ($env:LLAMA_SERVER_BIN) {
    Write-Host ("ok   {0,-16} {1}" -f "llama-server", $env:LLAMA_SERVER_BIN)
} else {
    Write-Host ("miss {0,-16} not found" -f "llama-server")
}

Write-Host ""
foreach ($path in @(
    $env:LLM_ROOT,
    $env:LLAMA_CPP_ROOT,
    $env:LLM_MODELS_DIR,
    $env:LLM_VENV_DIR
)) {
    if (Test-Path $path) {
        Write-Host "ok   $path"
    } else {
        Write-Host "miss $path"
    }
}

if ($missing -gt 0) {
    Write-Error "$missing required command(s) are missing."
}
