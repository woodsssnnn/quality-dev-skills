# PRD 修订工作流 (RV1-RV5)

> PRD 是需求源头，任何修改都必须经过版本化修订流程。AI 绝不可自行修改 PRD 文件。

## 触发条件

### 被动触发（自动检测）

| 触发场景 | 检测方式 |
|---------|--------|
| Gate 2 S4 verifier 发现 PRD 描述与实际业务不符 | verifier 报告 PRD-ERROR |
| 用户主动更新 PRD 目录中的文件 | P0/S0 PRD diff 检测（对比 revision-log.md） |
| PM 顾问 P1.7 发现 PRD 自相矛盾 | PM ISSUE (D1/D3) |
| `--analyze` AC1 发现 PRD→Plan MISSING | 分析报告 |
| Bug 修复过程中发现需求遗漏 | S4 Bug Log 分析 |

### 正向触发（用户主动声明）

用户在 Gate 2 执行中主动声明 PRD 有变更时，使用 `--prd-changed` 参数：

```
python gate-enforcer.py prd-changed --impact cosmetic|minor|major [--scope §X.X]
```

| 参数 | 说明 |
|------|------|
| `--impact cosmetic` | 纯表述修正（错别字/格式），不影响功能规格 |
| `--impact minor` | 功能规格微调，影响 ≤2 章节且 ≤5 可验证项 |
| `--impact major` | 结构性变更（新增/删除章节、业务逻辑大改） |
| `--scope §X.X` | 可选，声明具体变更的 PRD 章节 |

正向触发后引擎自动按影响级别处理下游（详见下方 RV5 正向触发路径）。

---

## RV1: 提出修订提案

```
触发：代理检测到 PRD 问题
输出：docs/prd/{feature}/proposals/prp-{date}-{简述}.md
状态：PROPOSED
```

### PRP 文件格式

```markdown
# PRD Revision Proposal

**PRP ID**: prp-2026-06-18-section-2-3-fix
**PRD**: docs/prd/user-auth/
**PRD Version**: v1.0.0.0
**Date**: 2026-06-18
**Status**: PROPOSED
**Proposed By**: Gate 2 S4 verifier / PM 顾问 P1.7 / 用户

## 问题描述
[具体描述 PRD 中的问题]

## 建议修订
[建议的修改内容]

## 涉及章节
- §2.3 [章节名]

## 涉及资产
- images/ui-reset-password.png
- tables/password-rules.md
```

---

## RV2: 影响分析

```
触发：RV1 完成
输入：PRP 文件
输出：docs/reports/prd-impact-{date}-{prp-id}.md
状态：ANALYZED
```

### 影响分级逻辑

正向触发时，RV2 嵌入影响分级判断：

| 影响级别 | 判断标准 | 下游处理路径 |
|---------|---------|------------|
| **cosmetic** | 仅涉及文字措辞/错别字/格式；不涉及字段名/枚举值/逻辑条件 | 仅标记 Plan 受影响章节为 NEEDS_REVIEW；Verification JSON 不变；不重跑 Gate |
| **minor** | 涉及 ≤2 个 PRD 章节；影响的 verification item ≤5 个；无新增/删除章节 | Plan 受影响章节重验（增量 Gate 1）；受影响 verification item 重置为 NEEDS_REVIEW |
| **major** | 新增/删除 PRD 章节；业务逻辑大改；影响 >5 个 verification item | 全量重跑 Gate 1；等同于 RV5 完整流程 |

### 影响分析步骤

1. **Plan 影响**：通过 §X.X 引用映射，找出受影响的 Plan 章节
   - 扫描 `docs/plans/{feature}/ch-*/README.md` 中的 PRD section 引用
   - 列出受影响的 unit 和可验证项

2. **Verification 影响**：查找受影响的 verification JSON item
   - 扫描 `docs/verification/` 中对应 unit 的 JSON 文件
   - 列出 status 需要重置为 NEEDS_REVIEW 的 item

3. **Code 影响**：通过 codeRefs 反查受影响的代码
   - 从 verification JSON 的 codeRefs 字段提取文件路径
   - 列出可能需要修改的代码文件

4. **PRD 资产影响**：列出受影响的图片/表格/附件
   - 从 PRD README.md frontmatter 的 sections.assets 字段提取

### 影响报告格式

使用 `report-templates.md` 的 **PRD Revision Impact Report** 模板，写入 `docs/reports/prd-impact-{date}-{prp-id}.md`。

注册到 `reports/INDEX.md` 和 `QGW-INDEX.md`。

---

## RV3: 人工审批（强制）

```
触发：RV2 完成
输入：PRP + 影响报告
行为：向用户展示修订内容 + 影响范围 + 建议处理方式
```

### 用户选项

| 选项 | 行为 |
|------|------|
| **A. 批准修订** | 继续 RV4 |
| **B. 驳回修订** | PRP 标记 REJECTED，记录驳回理由 |
| **C. 修改后批准** | 用户修改 PRD 后，代理重做 RV2 |

### ⚠️ 核心约束

- **AI 绝不可自行修改 PRD 目录中的任何文件**
- AI 可以：提供修改建议文本、指出需要修改的位置、生成修改后的文本供用户复制
- AI 不可以：使用 Write/Edit 工具修改 PRD 文件、删除 PRD 文件、重命名 PRD 文件

---

## RV4: 执行修订

```
触发：RV3 批准
行为：用户修改 PRD 目录内容
输出：PRD 版本号递增
状态：REVISED
```

### 用户操作

1. 修改 PRD 目录中的相关文件
2. 如有新增图片/表格，放入对应子目录
3. 更新 `README.md` frontmatter 中的 `prd-version` 和 `last-revised`

### PRD 版本格式

```html
<!-- PRD-REVISION: v1.1.0.0 | 2026-06-18T10:30:00Z | approved-by: user | reason: §2.3 笔误修正 | assets-changed: [images/ui-reset.png] -->
```

版本号规则：
- **Major 递增**：需求结构性变更（新增/删除章节，业务逻辑大改）
- **Minor 递增**：功能性修订（某章节的规则修改）
- **Patch 递增**：澄清性修订（笔误修正、细节补充）
- **Iteration 递增**：同一修订的多次调整

---

## RV5: 下游同步

```
触发：RV4 完成
行为：按 CP-1 变更传播规则同步下游文档
状态：SYNCED
```

### 正向触发路径（按影响级别分支）

当通过 `--prd-changed` 正向触发时，RV5 按影响级别走不同路径：

| 影响级别 | 路径 |
|---------|------|
| **cosmetic** | 仅标记 Plan 受影响章节为 NEEDS_REVIEW → 更新 QGW-INDEX → 记录到 Session Summary |
| **minor** | 标记 Plan + Verification item 为 NEEDS_REVIEW → 增量重验受影响项 → 更新 QGW-INDEX → 记录到 Session Summary |
| **major** | 全量重置 Gate 2 步骤（S1-S5） → 建议全量重跑 Gate 1 → 更新 QGW-INDEX → 记录到 Session Summary |

引擎通过 `prd-changed` 子命令自动执行步骤重置，代理只需完成文档更新部分。

### 传统同步步骤

1. **标记 Plan**：受影响章节的 unit 状态标记为 `NEEDS_REVIEW`
   - 修改 `docs/plans/{feature}/00-overview.md` 中对应 chapter 的 status

2. **标记 Verification**：受影响 item 状态重置
   - 修改 `docs/verification/unit-*.json` 中对应 item 的 status 为 `NEEDS_REVIEW`

3. **更新 QGW-INDEX**：PRD 版本号、修订次数
   - 修改 `docs/QGW-INDEX.md` 的 PRD Documents 表

4. **更新 revision-log.md**：追加修订记录
   ```markdown
   | v1.1.0.0 | 2026-06-18 | user | minor | §2.3 | Plan ch-2.3 NEEDS_REVIEW, 3 items affected |
   ```

5. **询问用户**：
   - 增量重跑 Gate 1（只处理 NEEDS_REVIEW 的章节）
   - 全量重跑 Gate 1
   - 标记待处理（后续手动决定）

6. **写入 Session Summary**：记录 PRD 修订事件到 Bug Log 或 Decisions 表

---

## revision-log.md 格式

```markdown
# PRD Revision Log: {feature-name}

| Version | Date | Approved By | Type | Sections Changed | Downstream Impact |
|---------|------|-------------|------|-----------------|-------------------|
| v1.0.0.0 | 2026-06-01 | — | initial | — | — |
| v1.1.0.0 | 2026-06-18 | user | minor | §2.3 | Plan ch-2.3 NEEDS_REVIEW, 3 items |
```

---

## 简化路径（minor 修订）

当修订类型为 `patch`（笔误修正、细节补充）时，可走简化路径：

- 跳过 RV2 完整影响分析（仅做 Plan 章节匹配，不做 Code 反查）
- RV3 仍需人工确认（不可跳过）
- RV5 仅标记 Plan，不标记 Verification

判断标准：PRP 的 `涉及章节` ≤ 1 个 且 `涉及资产` = 0
