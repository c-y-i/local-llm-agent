# Shared Windows defaults for local-llm-agent. Dot-source this file.

$ErrorActionPreference = "Stop"

if (-not $env:LOCAL_LLM_AGENT_ROOT) {
    $env:LOCAL_LLM_AGENT_ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
$repoRoot = (Resolve-Path $env:LOCAL_LLM_AGENT_ROOT).Path
$envFile = Join-Path $repoRoot ".env"

if (Test-Path $envFile) {
    foreach ($rawLine in Get-Content $envFile) {
        $line = $rawLine.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            continue
        }
        if ($line.StartsWith("export ")) {
            $line = $line.Substring(7).Trim()
        }
        $parts = $line.Split("=", 2)
        $name = $parts[0].Trim()
        $value = $parts[1].Trim()
        if ($name -notmatch "^[A-Za-z_][A-Za-z0-9_]*$") {
            continue
        }
        if ($value.Length -ge 2 -and $value[0] -eq $value[-1] -and $value[0] -in @("'", '"')) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        $value = [Environment]::ExpandEnvironmentVariables($value)
        $value = [regex]::Replace(
            $value,
            '\$\{([A-Za-z_][A-Za-z0-9_]*):-([^}]*)\}',
            {
                param($match)
                $resolved = [Environment]::GetEnvironmentVariable($match.Groups[1].Value)
                if ($resolved) { $resolved } else { $match.Groups[2].Value }
            }
        )
        $value = [regex]::Replace(
            $value,
            '\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)',
            {
                param($match)
                $key = if ($match.Groups[1].Success) {
                    $match.Groups[1].Value
                } else {
                    $match.Groups[2].Value
                }
                $resolved = [Environment]::GetEnvironmentVariable($key)
                if ($resolved) { $resolved } else { $match.Value }
            }
        )
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

if (-not $env:LLM_ROOT) {
    $env:LLM_ROOT = Join-Path $HOME "LLM"
}
if ($env:LLM_ROOT.StartsWith("~")) {
    $env:LLM_ROOT = Join-Path $HOME $env:LLM_ROOT.Substring(1).TrimStart("\", "/")
}
$env:LLAMA_CPP_ROOT = if ($env:LLAMA_CPP_ROOT) { $env:LLAMA_CPP_ROOT } else { Join-Path $env:LLM_ROOT "llama.cpp" }
$env:OLLAMA_ROOT = if ($env:OLLAMA_ROOT) { $env:OLLAMA_ROOT } else { Join-Path $env:LLM_ROOT "ollama" }
$env:LLM_MODELS_DIR = if ($env:LLM_MODELS_DIR) { $env:LLM_MODELS_DIR } else { Join-Path $env:LLM_ROOT "models" }
$env:OLLAMA_MODELS = if ($env:OLLAMA_MODELS) { $env:OLLAMA_MODELS } else { Join-Path $env:OLLAMA_ROOT "models\llm" }
$env:HF_HOME = if ($env:HF_HOME) { $env:HF_HOME } else { Join-Path $env:LLM_ROOT "huggingface" }
$env:STRATA_HOME = if ($env:STRATA_HOME) { $env:STRATA_HOME } else { Join-Path $env:LLM_ROOT "strata" }
$env:STRATA_MODELS_DIR = if ($env:STRATA_MODELS_DIR) { $env:STRATA_MODELS_DIR } else { Join-Path $env:LLM_ROOT "models\strata" }
$env:LLM_VENV_DIR = if ($env:LLM_VENV_DIR) { $env:LLM_VENV_DIR } else { Join-Path $env:LLM_ROOT ".venv" }
$env:LLM_RUN_DIR = if ($env:LLM_RUN_DIR) { $env:LLM_RUN_DIR } else { Join-Path $env:LLM_ROOT "run" }
$env:LLM_CODEX_HOME = if ($env:LLM_CODEX_HOME) { $env:LLM_CODEX_HOME } else { Join-Path $env:LLM_ROOT "codex-local" }
$env:LLM_HERMES_HOME = if ($env:LLM_HERMES_HOME) { $env:LLM_HERMES_HOME } else { Join-Path $env:LLM_ROOT "hermes-local" }
$env:LLAMA_CPP_HOST = if ($env:LLAMA_CPP_HOST) { $env:LLAMA_CPP_HOST } else { "127.0.0.1" }
$env:LLAMA_CPP_PORT = if ($env:LLAMA_CPP_PORT) { $env:LLAMA_CPP_PORT } else { "8080" }
$env:OLLAMA_HOST = if ($env:OLLAMA_HOST) { $env:OLLAMA_HOST } else { "127.0.0.1:11434" }

foreach ($name in @(
    "LLM_ROOT",
    "LLAMA_CPP_ROOT",
    "OLLAMA_ROOT",
    "LLM_MODELS_DIR",
    "OLLAMA_MODELS",
    "HF_HOME",
    "STRATA_HOME",
    "STRATA_MODELS_DIR",
    "LLM_VENV_DIR",
    "LLM_RUN_DIR",
    "LLM_CODEX_HOME",
    "LLM_HERMES_HOME"
)) {
    $value = [Environment]::GetEnvironmentVariable($name)
    if ($value -and $value.StartsWith("~")) {
        [Environment]::SetEnvironmentVariable(
            $name,
            (Join-Path $HOME $value.Substring(1).TrimStart("\", "/")),
            "Process"
        )
    }
}

if (-not $env:LLAMA_SERVER_BIN) {
    $candidates = @(
        (Join-Path $env:LLAMA_CPP_ROOT "build\bin\llama-server.exe"),
        (Join-Path $env:LLAMA_CPP_ROOT "build\bin\Release\llama-server.exe"),
        (Join-Path $env:LLAMA_CPP_ROOT "build\bin\Release\llama.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $env:LLAMA_SERVER_BIN = $candidate
            break
        }
    }
}

$env:LLAMA_CPP_BASE_URL = if ($env:LLAMA_CPP_BASE_URL) {
    $env:LLAMA_CPP_BASE_URL
} else {
    "http://$($env:LLAMA_CPP_HOST):$($env:LLAMA_CPP_PORT)"
}
$env:OLLAMA_BASE_URL = if ($env:OLLAMA_BASE_URL) {
    $env:OLLAMA_BASE_URL
} else {
    "http://$($env:OLLAMA_HOST)"
}
