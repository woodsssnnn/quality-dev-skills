@echo off
REM governance SessionStart hook wrapper (Windows) — 判题机完整性检测
REM
REM 复用 run-checks.cmd 验证过的模式：
REM   - hooks.json 里 command 无引号 ${CLAUDE_PLUGIN_ROOT}/hooks/integrity-check.cmd
REM   - .cmd 内部用 %~dp0（脚本自身目录）定位 integrity-check.js
REM   - exit /b %ERRORLEVEL% 透传退出码
REM
REM integrity-check.js 永远 exit 0（绝不阻断会话启动），ok/skip 静默，仅 drift 告警。

node "%~dp0integrity-check.js"
exit /b %ERRORLEVEL%
