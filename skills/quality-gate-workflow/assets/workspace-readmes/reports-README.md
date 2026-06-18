# docs/reports/ — 审计与验证报告

本目录存放质量门禁产出的各类报告。每个报告都是生命周期的节点，必须注册到 INDEX.md。

## 报告类型

| 类型 | 命名格式 | 产出阶段 | 工作流节点 |
|------|---------|---------|----------|
| Plan 完整性报告 | `completeness-{date}-{feature}.md` | Gate 1 P3 后 | P3-Report |
| Gate 1 Verifier 报告 | `gate1-verifier-{date}-{feature}.md` | Gate 1 P4 后 | P4-Report |
| 审计报告 | `audit-{date}-{Plan名称}.md` | Gate 2 Audit | S5-C |
| 修复验证报告 | `debug-{date}-{Bug描述}.md` | Gate 2 Debug D4 后 | D4-Report |
| 分析报告 | `analyze-{date}.md` | `--analyze` AC5 | AC5 |
| 自检报告 | `self-check-{date}-{session}.md` | `--self` SC5 | SC5 |
| PRD 影响报告 | `prd-impact-{date}-{prp-id}.md` | PRD Revision RV2 | RV2 |
| 回归测试报告 | `regression-{date}.md` | 定期回归 | 手动触发 |

## 报告模板

所有报告的格式模板在 `~/.agents/skills/quality-gate-workflow/assets/report-templates.md`。

## INDEX.md

每个报告生成后必须追加到 `INDEX.md`：

| 日期 | 类型 | 文件 | 关联 Plan/PRD | 触发 | 结果 |
|------|------|------|---------------|------|------|
| 2026-06-18 | completeness | [link] | feat-07 | Gate 1 P3 | PASS |

同时注册到 `docs/QGW-INDEX.md` 的 Reports 表。

未完成注册 = 反模式 #53。
