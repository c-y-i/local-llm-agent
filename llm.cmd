@echo off
setlocal
set "LLM_PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%LLM_PYTHON%" set "LLM_PYTHON=%USERPROFILE%\LLM\.venv\Scripts\python.exe"
if not exist "%LLM_PYTHON%" (
  echo Managed Python environment not found: %LLM_PYTHON% 1>&2
  echo Run: powershell -ExecutionPolicy Bypass -File "%~dp0scripts\setup\install-llm.ps1" 1>&2
  exit /b 3
)
"%LLM_PYTHON%" "%~dp0llm" %*
exit /b %ERRORLEVEL%
