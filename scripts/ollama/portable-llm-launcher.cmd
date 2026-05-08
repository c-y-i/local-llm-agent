@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0portable-llm-launcher.ps1" %*
exit /b %ERRORLEVEL%
