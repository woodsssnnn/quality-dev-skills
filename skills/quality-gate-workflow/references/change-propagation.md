# 文档变更传播规则 (CP-1 ~ CP-5)

> 任何文档变更都必须按传播规则更新下游依赖，禁止孤立修改。

## 规则概览

| 规则 | 触发 | 强制传播 | 不传播 |
|------|------|---------|--------|
| **CP-1** | PRD 修订 | Plan, Verification, QGW-INDEX | 已 PASS 且不受影响的 unit |
| **CP-2** | Plan 修订 | Verification, QGW-INDEX | 已 PASS 且不受影响的 unit |
| **CP-3** | Code 修复 | Verification, Plan Task 状态 | PRD, 其他文档 |
| **CP-4** | Report 生成 | QGW-INDEX, reports/INDEX | 无（终端产物） |
| **CP-5** | Error Pattern 升级 | dev_rule_path | 需人工确认后 promote 到全局层 |

---

## CP-1: PRD 修订传播

**触发**：PRD 版本从 vX.Y → vX.Y+1（由 RV5 触发）

### 强制传播项

```
1. Plan 受影响章节 → 标记 NEEDS_REVIEW
   位置：docs/plans/{feature}/00-overview.md 中 chapters[].status
   操作：status: "planned"|"verified" → "needs_review"

2. Verification JSON → 标记 NEEDS_REVIEW
   位置：docs/verification/unit-*.json 中受影响 item
   操作：status: "PASS"|"PENDING" → "NEEDS_REVIEW"

3. QGW-INDEX → 更新 PRD 版本号
   位置：docs/QGW-INDEX.md PRD Documents 表
   操作：更新 version 和 revision-count 列

4. reports/INDEX.md → 注册影响报告
   位置：docs/reports/INDEX.md
   操作：追加 prd-impact 报告行

5. Session Summary → 记录修订事件
   位置：docs/sessions/{session-id}.md Decisions 表
   操作：追加 PRD 修订决策记录
```

### 禁止事项

- ❌ 禁止自动修改已 PASS 且不受影响的 unit 的 Verification JSON
- ❌ 禁止自动回滚已提交的代码（代码影响由用户决定是否重跑 Gate 2）

---

## CP-2: Plan 修订传播

**触发**：Plan 在 feedback loop 中被修改（由 Gate 1 反馈回路或 Gate 2 S2.5 边界检查触发）

### 强制传播项

```
1. Verification JSON → 受影响 item 重置为 PENDING
   位置：docs/verification/unit-*.json
   操作：status → "PENDING"（仅重置受 PLAN 根因影响的 item）

2. QGW-INDEX → 更新 Plan 版本号
   位置：docs/QGW-INDEX.md Plan Documents 表
   操作：更新 plan-version 列

3. Session Summary → Decisions 表追加记录
   位置：docs/sessions/{session-id}.md
   操作：追加 Plan 修订决策（含 QGW-VERSION 标记）

4. Plan QGW-VERSION 标记
   位置：Plan 文档内部
   操作：追加 <!-- QGW-VERSION: vX.Y | timestamp | reason: ... -->
```

### 条件传播项

```
if 修订涉及 allowedChanges/forbiddenChanges 变更:
    → 更新 Plan 文档中的变更范围声明
    → Gate 2 S2.5 boundary check 使用新范围

if 修订新增/删除 unit:
    → 创建/删除对应的 verification JSON 文件
    → 更新 00-overview.md 的 chapters 列表
```

### 禁止事项

- ❌ 禁止修改已 PASS 且无 PLAN 根因的 unit
- ❌ 禁止不追加 QGW-VERSION 就修改 Plan（反模式 #32）

---

## CP-3: Code 修复传播

**触发**：Gate 2 S4 verifier 报告 FAIL，根因分类为 CODE

### 强制传播项

```
1. Verification JSON → 更新 item status + codeRefs
   位置：docs/verification/unit-*.json
   操作：修复后更新 status → "PASS"，更新 codeRefs 和 commitSha

2. Plan 文档 → 更新 Task 状态 + Gate 2 实现记录
   位置：docs/plans/{feature}/ch-*/unit-*-impl.md
   操作：Task 状态标记、Gate 2 实现记录追加
```

### 不传播

- Plan 的可验证项定义不变（CODE 根因不改 Plan 规格）
- PRD 不受影响
- 其他 unit 不受影响

### 禁止事项

- ❌ 禁止 over-fixing：修改超出回归边界的代码（反模式 #20）
- ❌ 禁止不更新 Plan Task 状态就完成 Gate 2（反模式 #47）

---

## CP-4: Report 生成传播

**触发**：任何报告文件被创建

### 强制传播项

```
1. reports/INDEX.md → 注册报告
   位置：docs/reports/INDEX.md
   操作：追加一行（日期/类型/文件链接/关联/触发/结果）

2. QGW-INDEX → Document Registry 注册
   位置：docs/QGW-INDEX.md Reports 表
   操作：追加报告行
```

### 不传播

- Report 是终端产物，不触发下游变更
- Report 不修改 PRD、Plan、Verification 的内容

---

## CP-5: Error Pattern 升级传播

**触发**：工作空间层 error-patterns.json 中某 pattern 的 frequency 达到阈值

### 阈值规则

| frequency | 升级目标 |
|-----------|---------|
| ≥ 3 | 升级到项目 `dev_rule_path`（项目级开发规范） |
| ≥ 5 | 升级到 `gate_dev_rules`（Gate 配置） |
| ≥ 8 | 升级到 Red Lines / 合理化借口表 |

### 强制传播项

```
1. dev_rule_path → 追加规则
   位置：项目 dev-rule 技能文件
   操作：追加编码/设计规范条目

2. Session Summary → 记录升级事件
   位置：docs/sessions/{session-id}.md Decisions 表
```

### 条件传播项（需人工确认）

```
if 全局层 promote 条件满足（≥3 工作空间 + 用户确认）:
    → 升级到 references/error-patterns.json（全局层）
    → ⚠️ 必须用户确认后执行，不可自动 promote
```

### 禁止事项

- ❌ 禁止自动 promote 到全局层（反模式 #17）
- ❌ 禁止跳过 evolve 检查（反模式 #19）

---

## 传播检查清单

每次文档变更后，代理必须检查：

```markdown
## 变更传播检查

- [ ] 确定变更类型（PRD/Plan/Code/Report/ErrorPattern）
- [ ] 识别适用的传播规则（CP-1 ~ CP-5）
- [ ] 执行所有强制传播项
- [ ] 评估条件传播项是否适用
- [ ] 确认无禁止事项被违反
- [ ] 更新 QGW-INDEX 和 reports/INDEX（如适用）
```

未完成传播检查就继续下一步 = 反模式 #54。
