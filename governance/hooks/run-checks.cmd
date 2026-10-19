@echo off
REM governance PostToolUse hook wrapper (Windows)
REM
REM 宿主执行 hook 的 command 时，${CLAUDE_PLUGIN_ROOT} 不加引号才能正确展开
REM （加引号 "..." 会导致变量不展开 → 文件找不到 → hook 静默失败）。
REM hooks.json 里写无引号版：${CLAUDE_PLUGIN_ROOT}/hooks/run-checks.cmd
REM
REM .cmd 内部用 %~dp0（脚本自身目录）定位 run-checks.js —— 最可靠，
REM 不依赖环境变量。

node "%~dp0run-checks.js"
exit /b %ERRORLEVEL%
