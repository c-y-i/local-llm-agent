@echo off
call "%~dp0llm.cmd" agent hermes -- %*
exit /b %ERRORLEVEL%
