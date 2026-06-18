# 进度输出格式

> 本文档由 SKILL.md 路由按需加载（首次输出日志前）。

## 统一日志格式

所有步骤必须使用结构化日志格式：

```
[qgw][{timestamp}][{platform}:{session_id}][{gate}][{step}/{total}] {status} {message}
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `[qgw]` | 固定前缀 | `[qgw]` |
| `{timestamp}` | ISO时间戳 | `2026-06-17T20:45:00` |
| `{platform}` | 平台标识 | `mimo` / `claude` / `codex` / `opencode` |
| `{session_id}` | 完整会话ID | `ses_12ca2c1c4ffe0S3HguaG7fosHN` |
| `{gate}` | 阶段 | `gate1` / `gate2` / `analyze` |
| `{step}/{total}` | 步骤进度 | `P1/5` / `S3/5` |
| `{status}` | 状态图标 | ✅ / ❌ / ⚠️ / 🔄 / → |
| `{message}` | 消息内容 | `解析需求完成: 99项可验证项` |

## 平台标识

| 平台 | 标识 | 会话存储位置 | 类型 |
|------|------|--------------|------|
| MiMoCode | `mimo` | `~/.local/share/mimocode/memory/sessions/` | 国内 |
| 通义灵码 | `tongyi` | `~/.local/share/tongyi/sessions/` | 国内 |
| 豆包MarsCode | `marscode` | `~/.local/share/marscode/sessions/` | 国内 |
| 百度Comate | `comate` | `~/.local/share/comate/sessions/` | 国内 |
| CodeGeeX | `codegeex` | `~/.local/share/codegeex/sessions/` | 国内 |
| Cursor | `cursor` | `~/.cursor/sessions/` | 国际 |
| Claude Code | `claude` | `~/.claude/projects/{project-slug}/` | 国际 |
| Codex | `codex` | `~/.codex/sessions/{year}/` | 国际 |
| OpenCode | `opencode` | `~/.opencode/sessions/` | 国际 |

## 状态图标

- ✅ 步骤完成
- ❌ 步骤失败
- ⚠️ 警告/发现ISSUE
- 🔄 步骤进行中
- → 步骤开始/转移

## 统计汇总

```
[qgw][{timestamp}][{platform}:{session_id}][{gate}][STATS] 📊 总耗时: {time} | 步骤: {done}/{total} | 通过率: {rate}%
```

## 复盘路径

```bash
# MiMoCode会话
cat ~/.local/share/mimocode/memory/sessions/{session_id}/checkpoint.md

# Claude Code会话
cat ~/.claude/projects/{project-slug}/conversations/{session-id}.json

# Codex会话
cat ~/.codex/sessions/2026/{session-id}/history.json
```

示例见 [gate1-workflow.md](gate1-workflow.md) 和 [gate2-workflow.md](gate2-workflow.md)。
