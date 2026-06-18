---
name: quality-gate-workflow
description: |-
  Use when user requests quality-gated development workflow for requirements-to-code traceability,
  or when implementing features that need full traceability from PRD to code.
  Triggers on explicit parameters only: --gate1, --gate2, --all, --self, --analyze.
allowed-tools:
  - Task
  - Agent
  - Read
  - Grep
  - Glob
  - Bash(git diff *)
  - Bash(git status *)
  - Bash(git log *)
metadata:
  version: 1.0
---

# 质量门禁工作流

需求开发全链路质量保障。两个 Gate 确保需求不丢失、代码不偏离。

- **Gate 1**：需求 → 验证过的 Plan + 验收清单
- **Gate 2**：Plan + 验收清单 → 验证过的 Code

## 快速开始

1. 安装技能：在 quality-dev-skills 仓库目录执行 `bash scripts/install.sh`（首次使用时参见仓库根目录 `BOOTSTRAP.md`）
2. 初始化工作区：`bash scripts/health-check.sh --init-workspace`
3. 选择触发参数：`--gate1`（需求→Plan）/ `--gate2`（Plan→代码）/ `--all`（全流程）/ `--self`（复盘）/ `--analyze`（一致性分析）
4. 可选修饰：`--strict` / `--lite` / `--incremental` / `--e2e` / `--fix`

> ⚠️ 必须显式带参数触发，不使用关键词自动触发。未安装时参见 `BOOTSTRAP.md`。

## 核心机制

- **五层防线**：提取验收标准 → **PM 顾问评议** → 写 plan → **架构师顾问评议** → 自验 → 独立 verifier 子代理
- **角色分工**：顾问判断"合不合理"（架构/业务），verifier 判断"对不对齐"（一致性）。两者不可互替
- **根因分类**：CODE（代码偏差，Gate 2 内修 ≤2 轮） / PLAN（计划偏差，反馈 Gate 1 硬顶 1 轮）
- **100% 通过才放行**，任何 FAIL 必须修复后重新验证

### Gate 1 步骤

P1 → P1.5(DB) → P1.6(代码链路) → P1.7(PM 顾问) → P2 → P2.5(架构师顾问) → P3 → P4(verifier) → P5

`--lite` 跳过 P1.5/P1.6/P1.7。`--bug`/`--opt` 可跳过 P1.7。

### 顾问 vs verifier 边界

| 角色 | 身份 | 何时 | 关心 | 输出 | 派发方式 |
|------|------|------|------|------|---------|
| PM 顾问 | 独立 AI Agent | P1.7 | 需求合理性 | ISSUE + 隐含需求 + 严重性 | Task/Agent 工具调用 |
| 架构师顾问 | 独立 AI Agent | P2.5 | plan 架构合理性 | ISSUE + 根因簇 + 修复策略 | Task/Agent 工具调用 |
| verifier | 独立 AI Agent | P4 / S4 | plan ↔ PRD / code ↔ plan 一致性 | COVERED/PARTIAL/MISSING | Task/Agent 工具调用 |

所有三个角色都是独立 AI Agent，通过 Task/Agent 工具派发，不可由主代理自演。
**仅跑 verifier = 漏判架构/业务层问题**。仅跑顾问 = 漏判覆盖度问题。

## 合理化借口表（反驳清单）

主代理可能跳过顾问评议的常见借口，每条已预先反驳：

| 主代理借口 | 反驳 |
|-----------|------|
| "需求很简单，顾问浪费 token" | 07 任务 plan v2.0 标 90 项 PASS，5 类 PM/架构层问题全漏检。简单 ≠ 不会漏 |
| "PM 顾问是产品专家，我是开发做不了" | PM 顾问是子代理角色，主代理扮演即可（环境无 subagent 时）。prompt 模板见 `advisor-templates.md` |
| "架构我自己判断就行" | 主代理有沉没成本（自己写的 plan），架构师顾问无沉没成本，判断更客观 |
| "顾问 ISSUE 我主观认为不重要" | 必须给出技术理由，由 P4 verifier 复核驳回合理性 |
| "顾问跳过等下次再补" | 跳过必须有显式理由 + 日志，禁止静默跳过（anti-pattern #25）|
| "环境无 Agent 工具，跳过吧" | 主代理可显式扮演顾问角色 + 物证链记录角色边界，不等同于跳过 |
| "顾问和 verifier 重复了" | 顾问问"合不合理"，verifier 问"对不对齐"，覆盖不同维度 |
| "这是 bug 修复，跳过顾问" | `--bug` 仅可跳过 PM 顾问的 D2/D4/D5；架构师顾问 A3（局部 vs 全局）仍必做 |

## 参数调用语法

用户消息中包含 `--gate1`/`--gate2`/`--all`/`--self` 参数时触发技能。不使用关键词自动触发。

### 一级参数：流程（必选其一）

| 参数 | 含义 |
|------|------|
| `--gate1` | Gate 1: 需求→Plan |
| `--gate2` | Gate 2: Plan→代码 |
| `--all` | 全流程 Gate 1+2 串行 |
| `--self` | 自检：复盘指定会话的 Gate 执行质量 |
| `--analyze` | 跨 artifact 一致性分析（只读） |

### 二级参数：模式（可选）

| 参数 | 含义 | 适用 |
|------|------|------|
| `--prd` | PRD 需求转 Plan（Gate 1 默认） | gate1, all |
| `--bug` | Bug 分析+修复计划 | gate1, all |
| `--opt` | 重构/优化规划 | gate1, all |
| `--impl` | 按 Plan 实现（Gate 2 默认） | gate2, all |
| `--audit` | 审计已有代码偏差 | gate2 |
| `--debug` | 无 Plan 的 bug 修复 | gate2 |

### 三级参数：修饰（可选，叠加）

| 参数 | 含义 | 适用 |
|------|------|------|
| `--strict` | 零偏差通过，否则阻断 | 任意 |
| `--fix` | 审计后自动修正偏差 | gate2 --audit |
| `--lite` | 轻量快速通道（跳过 P1.5/P1.6/P1.7） | gate1, all |
| `--incremental` | 增量验证（只验证变更影响的 item） | gate2, all |
| `--e2e` | E2E 行为验证（运行项目测试套件） | gate2, all |

**`--lite` 轻量快速通道**：适用于单文件/单函数改动、纯前端无 DB 变更、bug fix 改动 ≤3 处。流程简化为 P1→P2→P4→P5，跳过 P1.5（DB 调查）、P1.6（代码链路调查）、P1.7（PM 顾问）。

跳过 Gate 1 只能由用户决定（使用 `--gate2` 而非 `--all`），代理无权跳过。

### `--self` 自检模式

| 参数 | 含义 |
|------|------|
| `--self` | 复盘最近的 QGW 会话 |
| `--self <session-id>` | 复盘指定会话 |
| `--self <keyword>` | 按名称关键词定位会话 |

`--self` 检查步骤完整性、Verifier 执行、文件产物、Plan 质量。输出质量报告，不修改任何文件。

`--strict` 适用：任何高严重性问题 → FAIL。

**详细步骤** → [references/self-check-workflow.md](references/self-check-workflow.md)

**示例**：`"自检 --self"` / `"复盘上个会话 --self 0610-tcl"` / `"严格自检 --self --strict"`

**Gate 1/2 详细步骤** → [references/gate1-workflow.md](references/gate1-workflow.md) | [references/gate2-workflow.md](references/gate2-workflow.md)

**示例**：`"实现SP1 --gate2"` / `"审计报表 --gate2 --audit --fix"` / `"全流程 --all --strict"`

## 进度输出

**统一格式**：所有步骤必须使用结构化日志格式：

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

**平台标识**：

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

**状态图标**：
- ✅ 步骤完成
- ❌ 步骤失败
- ⚠️ 警告/发现ISSUE
- 🔄 步骤进行中
- → 步骤开始/转移

**统计汇总**：
```
[qgw][{timestamp}][{platform}:{session_id}][{gate}][STATS] 📊 总耗时: {time} | 步骤: {done}/{total} | 通过率: {rate}%
```

**复盘路径**：
```bash
# MiMoCode会话
cat ~/.local/share/mimocode/memory/sessions/{session_id}/checkpoint.md

# Claude Code会话
cat ~/.claude/projects/{project-slug}/conversations/{session-id}.json

# Codex会话
cat ~/.codex/sessions/2026/{session-id}/history.json
```

示例见 [references/gate1-workflow.md](references/gate1-workflow.md) 和 [references/gate2-workflow.md](references/gate2-workflow.md)。

## 红线 - 停下来重新开始

**违反规则的字面意思就是违反规则的精神。**

- 跳过 verifier 验证（#1/#2）
- 静默跳过顾问评议（#25）
- 验收标准模糊（#5）— "有筛选功能" ❌，"筛选器=流程树多选 (§6.1.1)" ✅
- 需求猜测（#6）— 不问用户就解读需求
- 凭记忆提取标准（#8）— 不读文件就写 plan
- over-fixing（#20）— 修改超出回归边界
- 顾问自演（#27）— 主代理扮演顾问角色

**以上任何一条都意味着：返回上一步，重新执行。禁止继续。**

## 常见错误与禁止行为

完整 46 条规则见 [references/anti-patterns.md](references/anti-patterns.md)。最常违规的：跳过 verifier（#1/#2）、验收标准模糊（#5）、需求猜测（#6）、凭记忆提取（#8）、over-fixing（#20）、顾问静默跳过（#25）、`--lite` 滥用（#26）、顾问自演（#27）。

## Knowledge Compounding（自进化）

每个 Unit 完成后执行 evolve 检查（无 FAIL 也确认"无新增 pattern"）。

| 层级 | 位置 | 写入规则 |
|------|------|---------|
| **工作空间层** | `docs/verification/error-patterns.json` | verifier 发现新 FAIL/PARTIAL 模式后自动提取 |
| **全局层** | `references/error-patterns.json` | 仅人工 promote（≥3 工作空间 + 用户确认） |

工作空间层模式累计达阈值时（3/5/8），升级到项目 `dev_rule_path` / `gate_dev_rules` / Red Lines / 合理化借口表。

## 项目配置

`.qgw/` 项目本地覆盖目录 + CLAUDE.md 兼容配置。详见 [references/project-config.md](references/project-config.md)。

## 安装

详见 [references/installation.md](references/installation.md)。

## 功能概览

功能概览详见 [references/feature-overviews.md](references/feature-overviews.md)。

## 参考文件索引

| 文件 | 内容 |
|------|------|
| [references/gate1-workflow.md](references/gate1-workflow.md) | Gate 1 P1→P5 详细步骤、Bug/Optimization 模式、反馈回路 |
| [references/gate2-workflow.md](references/gate2-workflow.md) | Gate 2 S0→S5、Schema 验证、Audit/Debug 模式、Compaction Recovery |
| [references/self-check-workflow.md](references/self-check-workflow.md) | Self-Check SC0→SC5、会话定位、日志提取、Plan 质量分析、报告生成 |
| [references/analyze-workflow.md](references/analyze-workflow.md) | Cross-Artifact 一致性分析 AC0→AC5 |
| [references/anti-patterns.md](references/anti-patterns.md) | 禁止行为完整规则（46 条去重） |
| [references/verifier-templates.md](references/verifier-templates.md) | Verifier 子代理 prompt 模板 + CROSS-CUTTING 横切检查清单 |
| [references/advisor-templates.md](references/advisor-templates.md) | PM 顾问 + 架构师顾问 prompt 模板 |
| [references/acceptance-criteria-schema.json](references/acceptance-criteria-schema.json) | 验收清单 JSON Schema v1.2（含 codeRefs/commitSha/clarifications）|
| [references/error-patterns.json](references/error-patterns.json) | 全局错误模式种子数据 |
| [references/regression-test-cases.md](references/regression-test-cases.md) | 回归测试用例集 |
| [references/constitution-template.md](references/constitution-template.md) | Gate 1 constitution 模板 |
| [evaluations/](evaluations/) | Skill 效果评估框架 |

## 版本记录

→ [CHANGELOG.md](CHANGELOG.md)
