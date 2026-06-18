# 安装指南

## 1. 放置技能文件

```
~/.agents/skills/quality-gate-workflow/   # 标准位置（推荐）
```

`~/.agents/skills/` 是通用技能目录标准。如果当前 AI 工具不支持此路径，将本目录软链接到工具的全局技能目录：

```bash
# 以 Claude Code 为例
ln -s ~/.agents/skills/quality-gate-workflow ~/.claude/skills/quality-gate-workflow
```

## 2. 工作空间初始化

Gate 1 P0 / Gate 2 S0 会自动检查并创建以下目录（无需手动运行脚本）：

- `docs/plans/` — 实现计划文档
- `docs/verification/` — 结构化验收数据（JSON Schema）
- `docs/reports/` — 审计报告、验证报告
- `docs/sessions/` — 会话摘要

## 3. Hook（默认安装）

Hook 在 git commit 前自动执行 7 项检查，确保：
- Plan 文档存在且 verification JSON 指向有效 Plan
- error-patterns 在 FAIL 发生后已创建
- QGW-INDEX.md 已维护
- 所有验收项有 source 引用和 toolCallId
- verifierReports 非空（物证链完整）
- 所有验收项已标记 PASS

安装（除非工具不支持 Hook，否则默认执行）：

> ⚠️ **前置依赖**：`hook-install.sh` 需要 **Python 3**（`python3` 或 `python`）做可靠的 JSON 操作，无 Python 会直接退出报错。Windows 用户请先确认 Python 已安装并在 PATH 中。

```bash
bash ~/.agents/skills/quality-gate-workflow/scripts/hook-install.sh
```

设置检查模式（可选）：

```bash
bash ~/.agents/skills/quality-gate-workflow/scripts/hook-install.sh --mode=strict  # 默认，阻止提交
bash ~/.agents/skills/quality-gate-workflow/scripts/hook-install.sh --mode=warn   # 只警告
bash ~/.agents/skills/quality-gate-workflow/scripts/hook-install.sh --mode=off    # 跳过检查
```

也可通过 `.claude/settings.local.json` 设置 `env.QGW_HOOK_MODE` 环境变量。

卸载：

```bash
bash ~/.agents/skills/quality-gate-workflow/scripts/hook-uninstall.sh
```

重新安装（先卸载再安装）：

```bash
bash ~/.agents/skills/quality-gate-workflow/scripts/hook-install.sh --force
```

> **为什么不默认自动安装？** 某些 AI 工具（如部分 Codex 环境、Cursor）不支持 Hook 机制。在这些环境中执行 install 会写入无效配置，因此首次使用时请人工确认工具支持后执行一次 `hook-install.sh`。
