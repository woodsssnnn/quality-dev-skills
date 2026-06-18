# 全部参数

> 本文档由 SKILL.md 路由按需加载（用户请求完整参数时）。

## 二级参数：模式（可选）

| 参数 | 含义 | 适用 |
|------|------|------|
| `--prd` | PRD 需求转 Plan（Gate 1 默认） | gate1, all |
| `--bug` | Bug 分析+修复计划 | gate1, all |
| `--opt` | 重构/优化规划 | gate1, all |
| `--impl` | 按 Plan 实现（Gate 2 默认） | gate2, all |
| `--audit` | 审计已有代码偏差 | gate2 |
| `--debug` | 无 Plan 的 bug 修复 | gate2 |

## 三级参数：修饰（可选，叠加）

| 参数 | 含义 | 适用 |
|------|------|------|
| `--strict` | 零偏差通过，否则阻断 | 任意 |
| `--fix` | 审计后自动修正偏差 | gate2 --audit |
| `--lite` | 轻量快速通道（跳过 P1.5/P1.6/P1.7） | gate1, all |
| `--incremental` | 增量验证（只验证变更影响的 item） | gate2, all |
| `--e2e` | E2E 行为验证（运行项目测试套件） | gate2, all |
| `--prd-changed` | 声明 PRD 有变更（影响级别: cosmetic/minor/major） | gate2 |
| `--plan-tweak` | Gate 2 执行中对 Plan 做轻量微调 | gate2 |

## `--lite` 轻量快速通道

适用于单文件/单函数改动、纯前端无 DB 变更、bug fix 改动 ≤3 处。流程简化为 P1→P2→P4→P5，跳过 P1.5（DB 调查）、P1.6（代码链路调查）、P1.7（PM 顾问）。

跳过 Gate 1 只能由用户决定（使用 `--gate2` 而非 `--all`），代理无权跳过。

## `--self` 自检模式

| 参数 | 含义 |
|------|------|
| `--self` | 复盘最近的 QGW 会话 |
| `--self <session-id>` | 复盘指定会话 |
| `--self <keyword>` | 按名称关键词定位会话 |

`--self` 检查步骤完整性、Verifier 执行、文件产物、Plan 质量。输出质量报告，不修改任何文件。

`--strict` 适用：任何高严重性问题 → FAIL。

**详细步骤** → [self-check-workflow.md](self-check-workflow.md)

**示例**：`"自检 --self"` / `"复盘上个会话 --self 0610-tcl"` / `"严格自检 --self --strict"`

## Gate 1/2 详细步骤

→ [gate1-workflow.md](gate1-workflow.md) | [gate2-workflow.md](gate2-workflow.md)

**示例**：`"实现SP1 --gate2"` / `"审计报表 --gate2 --audit --fix"` / `"全流程 --all --strict"` / `"快速修复 --preset quickfix"`

## 参数组合矩阵

| 组合 | 效果 |
|------|------|
| `--gate1 --prd` | 标准 PRD → Plan 流程 |
| `--gate1 --bug --lite` | 轻量 Bug 分析（跳过顾问） |
| `--gate2 --impl --incremental` | 增量实现（只验证变更项） |
| `--gate2 --debug --e2e` | Bug 修复 + E2E 验证 |
| `--all --strict --e2e` | 全流程严格模式 + E2E |
| `--gate2 --audit --fix` | 审计后自动修正 |
| `--gate2 --prd-changed --impact minor` | PRD 变更后增量重验 |
| `--gate2 --plan-tweak --scope ch-2.3` | Plan 轻量微调 |

## 参数互斥规则

| 互斥对 | 原因 |
|--------|------|
| `--lite` + `--strict` | lite 简化流程，strict 要求零偏差，逻辑矛盾 |
| `--bug` + `--audit` | 不同工作模式 |
| `--prd-changed` + `--plan-tweak` | 不同触发场景，不应同时使用 |
| `--incremental` + `--all` | incremental 仅适用 gate2 |
