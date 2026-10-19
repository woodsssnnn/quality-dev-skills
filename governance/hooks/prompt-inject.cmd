@echo off
REM governance UserPromptSubmit hook wrapper (Windows) — 语境提示注入
REM 复用 run-checks.cmd 验证过的模式（%~dp0 定位 + 透传退出码）。

node "%~dp0prompt-inject.js"
exit /b %ERRORLEVEL%
