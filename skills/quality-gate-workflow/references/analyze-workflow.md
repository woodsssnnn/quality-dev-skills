# Cross-Artifact 一致性分析工作流

手动触发的跨 artifact 一致性分析。只读操作，不修改任何文件，只产出报告。

## 目录
- [AC0：定位 artifacts](#ac0定位-artifacts)
- [AC1：PRD → Plan 覆盖分析](#ac1prid--plan-覆盖分析)
- [AC2：Plan → Verification 映射分析](#ac2plan--verification-映射分析)
- [AC3：Verification → Code 可追溯分析](#ac3verification--code-可追溯分析)
- [AC4：Cross-Unit 依赖分析](#ac4cross-unit-依赖分析)
- [AC5：Scope 完整性分析 + 报告生成](#ac5scope-完整性分析--报告生成)

---

## AC0：定位 artifacts

> 输出: `[qgw:analyze:AC0] 定位 artifacts ...` / `✅ N 个 artifact 已定位`

收集项目中所有 QGW 相关 artifact：

```bash
# PRD 文件
ls docs/prd/**/*.md 2>/dev/null

# Plan 文件
ls docs/plans/*.md 2>/dev/null

# Verification JSON
ls docs/verification/unit-*.json 2>/dev/null

# Session Summary
ls docs/sessions/*.md 2>/dev/null

# Master Index
ls docs/QGW-INDEX.md 2>/dev/null
```

对每个 artifact 记录：路径、生成时间、关联关系。

---

## AC1：PRD → Plan 覆盖分析

> 输出: `[qgw:analyze:AC1] PRD → Plan 覆盖 ...` / `✅ N/M 项 COVERED`

从 PRD 中提取所有 `§X.X` 章节引用，检查每个章节是否在 Plan 中有对应 unit。

**检查逻辑**：
1. 从 PRD 提取所有 `§X.X` 引用（正则 `§\d+\.\d+`）
2. 从 Plan 提取所有 `§X.X` 引用
3. 对比：PRD 有但 Plan 无 → MISSING

**输出格式**：

```
## PRD → Plan 覆盖
  COVERED: 12/15 项
  MISSING: 2 项
    - §6.3.5 (审批流程) — PRD 有描述，Plan 无对应 unit
    - §6.3.6 (退回逻辑) — PRD 有描述，Plan 无对应 unit
  AMBIGUOUS: 1 项
    - §6.1.3 (配置控制范围) — Plan 提及但描述模糊
```

---

## AC2：Plan → Verification 映射分析

> 输出: `[qgw:analyze:AC2] Plan → Verification 映射 ...` / `✅ N/M unit 已映射`

检查每个 Plan unit 是否有对应的 verification JSON 条目。

**检查逻辑**：
1. 从 Plan 提取所有 unit 名称
2. 从 `docs/verification/unit-*.json` 提取所有 unit 名称
3. Plan 有但 Verification 无 → ORPHANED

**输出格式**：

```
## Plan → Verification 映射
  COVERED: 12/12 unit
  ORPHANED: 0
```

或：

```
## Plan → Verification 映射
  COVERED: 10/12 unit
  ORPHANED: 2 unit
    - Unit 3: "审批流程" — Plan 有但 verification 无
    - Unit 4: "退回逻辑" — Plan 有但 verification 无
```

---

## AC3：Verification → Code 可追溯分析

> 输出: `[qgw:analyze:AC3] Verification → Code 可追溯 ...` / `✅ N/M 项 TRACEABLE`

检查每个 PASS 的 verification item 是否有 codeRefs 和 commitSha。

**检查逻辑**：
1. 遍历所有 verification JSON 中 status=PASS 的 item
2. 检查是否有 `codeRefs`（非空数组）
3. 检查是否有 `commitSha`（非空字符串）
4. 缺任一 → BROKEN

**输出格式**：

```
## Verification → Code 可追溯
  TRACEABLE: 10/12 项 (有 codeRefs + commitSha)
  BROKEN: 2 项
    - U1-03: 无 codeRefs — 无法追溯到代码变更
    - U1-07: 无 commitSha — 无法追溯到 git commit
```

---

## AC4：Cross-Unit 依赖分析

> 输出: `[qgw:analyze:AC4] Cross-Unit 依赖 ...` / `✅ 0 处未声明依赖`

检查 Unit 之间是否有未声明的依赖（unit A 改了 unit B 的 allowed 范围内的文件）。

**检查逻辑**：
1. 从每个 Plan unit 提取 `allowedChanges` 路径模式
2. 从每个 verification item 的 `codeRefs` 提取实际变更文件
3. 如果 unit A 的 codeRefs 文件匹配 unit B 的 allowedChanges → DEPENDENCY

**输出格式**：

```
## Cross-Unit 依赖
  DEPENDENCIES: 1 处
    - Unit 2 的 codeRefs 引用 src/components/Filter.tsx
      该文件在 Unit 1 的 allowedChanges 范围内
      → 建议：在 Unit 2 的 allowedChanges 中声明，或合并到 Unit 1
```

---

## AC5：Scope 完整性分析 + 报告生成

> 输出: `[qgw:analyze:AC5] Scope 完整性 ...` / `✅ 0 处 GAP` + 报告写入

检查 Plan 的 `allowedChanges` 是否覆盖所有 verification codeRefs 引用的文件。

**检查逻辑**：
1. 从所有 verification item 的 codeRefs 提取文件路径
2. 从对应 Plan unit 的 allowedChanges 提取路径模式
3. 文件路径不匹配任何 allowed 模式 → GAP

**输出格式**：

```
## Scope 完整性
  GAPS: 1 处
    - U1-05 codeRefs 引用 src/api/data.ts
      但 Plan Unit 1 的 allowed 只有 src/views/**
      → 建议：在 Plan 的 allowedChanges 中添加 src/api/**
```

### 报告生成

分析完成后，生成报告文件 `docs/reports/analyze-{date}.md`：

```markdown
## Cross-Artifact 一致性分析报告
Date: [YYYY-MM-DD]
Trigger: --analyze

### PRD → Plan
- COVERED: X/Y
- MISSING: N 项
- AMBIGUOUS: M 项

### Plan → Verification
- COVERED: X/Y
- ORPHANED: N 项

### Verification → Code
- TRACEABLE: X/Y
- BROKEN: N 项

### Cross-Unit
- DEPENDENCIES: N 处

### Scope 完整性
- GAPS: N 处

### 总体判定: PASS / FAIL
```

**`--strict` 模式**：任何 MISSING / BROKEN / DEPENDENCY / GAP → FAIL。
