@echo off
call "%~dp0llm.cmd" agent codex -- %*
exit /b %ERRORLEVEL%
