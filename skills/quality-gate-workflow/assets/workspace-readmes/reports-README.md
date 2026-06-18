# docs/reports/ — 审计与验证报告

本目录存放质量门禁产出的各类报告。

## 报告类型

| 类型 | 命名格式 | 产出阶段 |
|------|---------|---------|
| 审计报告 | `audit-<yyyy-MM-dd>-<Plan名称>.md` | Gate 2 Audit Mode |
| 修复验证报告 | `fix-<yyyy-MM-dd>-<Bug描述>.md` | Gate 2 Debug Mode |
| Plan 完整性报告 | `plan-completeness-<yyyy-MM-dd>-<需求名>.md` | Gate 1 Audit |
| 回归测试报告 | `regression-<yyyy-MM-dd>.md` | 定期回归 |

## 报告模板

所有报告的格式模板在 `~/.agents/skills/quality-gate-workflow/assets/report-templates.md`。

## 报告索引

| 日期 | 类型 | 关联 Plan/需求 | 结论 |
|------|------|---------------|------|
| ... | ... | ... | PASS/FAIL |

（手动维护此索引，或在每次生成报告时追加一行）
