@echo off
call "%~dp0llm.cmd" agent claude -- %*
exit /b %ERRORLEVEL%
