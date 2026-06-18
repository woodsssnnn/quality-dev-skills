# docs/plans/ — 实现计划文档

本目录存放质量门禁 Gate 1 产出的实现计划文档。

## 命名规则

| 类型 | 命名格式 | 示例 |
|------|---------|------|
| 新功能 | `feat-<需求编号>-<简要说明>.md` | `feat-07-process-track.md` |
| Bug 修复 | `BUG-<yyyy-MM-dd>-<需求编号>-<简要说明>.md` | `BUG-2026-06-09-07-附件显示.md` |
| 重构优化 | `refactor-<简要说明>.md` | `refactor-report-query-optimize.md` |

## 文档结构

每个 Plan 文档包含：

1. **头部**：目标、架构、技术栈
2. **任务分解**：SP1~SPN，每个任务含文件列表和具体步骤
3. **验收清单**（Gate 1 P5 追加）：`<!-- Appended by quality-gate-workflow Gate 1 -->`

## 验收清单格式

Plan 文档末尾会被自动追加验收清单。**不要手动编辑**追加部分。

```
<!-- Appended by quality-gate-workflow Gate 1 -->
## Acceptance Criteria Checklist
Source: [需求路径]
Generated: [日期]

### Unit 1: [名称]
- [ ] Item 1 (§X.X): [规格]
```

## 与 verification/ 的关系

每个 Plan 文件对应 `docs/verification/` 下的一个同名 JSON 文件，包含结构化的验收数据。Plan 文档是 Markdown 人类可读版，JSON 是机器可读版。
