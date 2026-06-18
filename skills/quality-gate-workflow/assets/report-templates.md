# 报告模板

## Gate 2 Audit Report

```markdown
## Audit Report: [Plan名称]

**日期**: [YYYY-MM-DD]
**Plan**: [plan 文件路径]
**PRD**: [需求文件路径]

### 汇总

| Unit | Verifier结论 | 偏差数 | 偏差详情 |
|------|-------------|--------|---------|
| Unit 1: [名称] | PASS | 0 | — |
| Unit 2: [名称] | FAIL | 3 | [偏差摘要] |

**总计**: X PASS / Y FAIL
**总体结论**: [PASS|FAIL]

### 逐 Unit 详情

#### Unit 1: [名称]
- 代码: [文件路径]
- 验收标准: X 项

| Criterion | PRD 引用 | 判定 | 证据 |
|-----------|---------|------|------|
| [标准描述] | §X.X | PASS | [代码引用] |
| [标准描述] | §X.X | FAIL | [偏差说明] → 根因: CODE/PLAN |

### 收敛修复记录（如有）

| Round | 修复项数 | 再验结果 | 剩余 |
|-------|---------|---------|------|
| 1 | N | [结果] | M |
| 2 | M | [结果] | K |
```

---

## Gate 1 Plan Completeness Report

```markdown
## Plan Completeness Report: [需求名称]

**日期**: [YYYY-MM-DD]
**需求**: [PRD 文件路径]
**Plan**: [plan 文件路径]

### 汇总

- COVERED: X 项
- MISSING: Y 项
- PARTIAL: Z 项
- AMBIGUOUS: W 项

**总体结论**: [PASS|FAIL]

### 逐项详情

| Item ID | 需求引用 | 计划章节 | 判定 | 说明 |
|---------|---------|---------|------|------|
| [id] | §X.X [原文] | §Y [计划内容] | COVERED | [匹配说明] |
| [id] | §X.X [原文] | — | MISSING | [应在计划何处出现] |
| [id] | §X.X [原文] | §Y [计划内容] | PARTIAL | [差距说明] |
| [id] | §X.X [原文] | — | AMBIGUOUS | [歧义描述] |

### 验收清单（已持久化到 Plan 文档）

[PASTE appended checklist]
```

---

## Debug Fix Verification Report

```markdown
## Fix Verification: [Bug描述]

**日期**: [YYYY-MM-DD]
**修复标准来源**: [bug 描述 / issue 链接]

### 修复标准

| 维度 | 标准 |
|------|------|
| 症状 | [什么错了] |
| 预期 | [修好后什么样] |
| 回归边界 | [什么不能变] |

### 验证结果

| 维度 | 判定 | 证据 |
|------|------|------|
| 症状消除 | PASS/FAIL | [证据] |
| 预期达成 | PASS/FAIL | [证据] |
| 回归完整 | PASS/FAIL | [证据] |
| 无 over-fixing | PASS/FAIL | [证据] |

**总体结论**: [PASS|FAIL]
```

---

## Session Summary

```markdown
# QGW Session: {session-id}
Date: [YYYY-MM-DD]
Trigger: [原始参数，如 --all --prd]

## Execution Flow
| Step | Status | Notes |
|------|--------|-------|
| P0 | ✅ | 工作空间就绪 |
| P1 | ✅ | N 项可验证项 |
| P1.5 | ⏭ SKIP | 跳过理由 |
| P1.6 | ✅ | M 个调用点 |
| P1.7 | ✅ | PM 顾问: K ISSUE |
| P2 | ✅ | L 个 unit |
| P2.5 | ✅ | 架构师顾问: J ISSUE |
| P3 | ✅ | 100% covered |
| P4 | ✅ | round N, toolCallId: Agent\|roundN\|... |
| P5 | ✅ | 验收清单已持久化 |
| S0-S2 | ✅ | — |
| S3 | ✅ | — |
| S4 | ✅ | round N |
| S5 | ✅ | 提交 [commit-sha] |

## Decisions
| Step | Decision | Rationale |
|------|----------|-----------|
| P1.5 | SKIP | [理由] |
| P2.5 | 接受 ARCH-N | [理由] |
| feedback | 修 Plan v1.1 | [PLAN 根因描述] |

## Bug Log
| ID | Type | Source | Description | Root Cause | Fix | Session |
|----|------|--------|-------------|------------|-----|---------|
| BUG-001 | PLAN | S4 verifier | [描述] | PLAN 根因 | Plan vX.X 修正 | [session-id] |
| BUG-002 | CODE | S4 verifier | [描述] | CODE 根因 | 代码修复 round N | [session-id] |

## Traceability
| Item | Code Refs | Commit |
|------|-----------|--------|
| U1-01 (§X.X) | [file:lines] | [commit-sha] |
| U1-02 (§X.X) | [file:lines] | [commit-sha] |
```

---

## Gate 1 Verifier Report

> 生成节点：Gate 1 P4 完成后
> 文件路径：`docs/reports/gate1-verifier-{date}-{feature}.md`

```markdown
## Gate 1 Verifier Report: [feature名称]

**日期**: [YYYY-MM-DD]
**PRD**: docs/prd/{feature}/
**Plan**: docs/plans/{feature}/
**Verifier**: [toolCallId]

### 汇总

- COVERED: X 项
- PARTIAL: Y 项
- MISSING: Z 项

**总体结论**: [COVERED|PARTIAL|MISSING]

### 逐章节详情

#### ch-{X.X}-{name}

| Item ID | PRD §X.X | Plan 对应 | 判定 | 证据/差距 |
|---------|----------|-----------|------|------------|
| U1-01 | §2.1 邮箱唯一 | ch-2.1 unit-1 V1.1 | COVERED | Plan 明确描述 |
| U1-02 | §2.1 角色枚举 | — | MISSING | Plan 未覆盖 |

### PRD 资产检查

| 资产 | 类型 | 已解析 | 与文字一致性 |
|------|------|--------|-------------|
| images/ui-register.png | 原型图 | ✅ | ✅ |
| tables/auth-rules.md | 数据字典 | ✅ | ⚠️ 不一致 |
```

---

## PRD Revision Impact Report

> 生成节点：PRD Revision RV2 完成后
> 文件路径：`docs/reports/prd-impact-{date}-{prp-id}.md`

```markdown
## PRD Revision Impact: [PRP ID]

**日期**: [YYYY-MM-DD]
**PRD**: docs/prd/{feature}/
**PRD Version**: v{old} → v{new}
**PRP**: docs/prd/{feature}/proposals/{prp-file}

### 修订摘要

[PRP 问题描述和建议修订的摘要]

### Plan 影响

| 章节 | Unit | 受影响项 | 当前状态 | 建议操作 |
|------|------|---------|---------|----------|
| ch-2.3 | unit-5 | V5.1, V5.2 | PASS | → NEEDS_REVIEW |
| ch-2.3 | unit-6 | V6.1 | PENDING | 无影响 |

### Verification 影响

| 文件 | 受影响 item | 当前 status | 建议操作 |
|------|------------|-------------|----------|
| unit-5.json | V5.1, V5.2 | PASS | → NEEDS_REVIEW |

### Code 影响

| 文件 | 行号 | 描述 |
|------|------|------|
| src/auth/ResetService.java | 42-58 | 密码重置逻辑可能受影响 |

### PRD 资产影响

| 资产 | 影响 |
|------|------|
| images/ui-reset.png | 需要更新 |

### 建议

- [ ] 增量重跑 Gate 1（仅 ch-2.3）
- [ ] 全量重跑 Gate 1
- [ ] 标记待处理
```
