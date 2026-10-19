@echo off
REM governance Stop hook wrapper (Windows) — 每轮统计（仅 stderr）
REM 复用 run-checks.cmd 验证过的模式（%~dp0 定位 + 透传退出码）。

node "%~dp0turn-stats.js"
exit /b %ERRORLEVEL%
