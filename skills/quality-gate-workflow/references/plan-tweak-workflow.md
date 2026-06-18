# Plan 微调工作流 (TW1-TW4)

> Gate 2 执行中对 Plan 做轻量微调，不触发全量重验。仅修改实现细节，不改可验证项定义。

## 适用场景

| 场景 | 示例 |
|------|------|
| Plan Task 描述修正 | 修正实现步骤中的笔误或措辞 |
| 实现顺序调整 | 调整 unit 之间的执行顺序 |
| 实现细节补充 | 补充遗漏的实现细节或技术选型说明 |
| 依赖关系微调 | 调整 unit 间的依赖声明 |

## 不适用场景（升级为 `--prd-changed`）

- 新增/删除可验证项
- 修改验收标准的定义
- 修改 allowedChanges / forbiddenChanges 范围
- 涉及 PRD 章节映射的变更

---

## TW1: 声明微调

```
触发：用户在 Gate 2 执行中声明需要微调 Plan
命令：python gate-enforcer.py plan-tweak --reason "原因" [--scope ch-X.X]
输出：引擎记录 tweak 到 state["plan_tweaks"]
```

### 前置条件

- 当前必须在 Gate 2（`gate == "gate2"`）
- 当前步骤必须在 S1-S3 之间（S4 verifier 之前）
- S4 不得已完成或正在执行

### 约束

- 微调只允许修改 Plan 的**实现细节**（Task 描述、实现顺序、技术选型）
- 不可修改**可验证项定义**（item id、验收标准、PRD section 引用）
- 如果微调涉及可验证项变更，引擎将 BLOCK 并建议升级使用 `--prd-changed`

---

## TW2: 影响分析

```
触发：TW1 完成
行为：分析微调对下游的影响
```

### 分析步骤

1. **识别受影响章节**：根据 `--scope` 参数匹配 Plan 中的章节
2. **检查可验证项**：确认受影响章节中的 item 定义不变
3. **评估 verifier 影响**：判断 S4 verifier 是否需要重新验证受影响项

### 影响判定

| 影响范围 | 处理方式 |
|---------|---------|
| 仅 Task 描述 | 标记受影响章节为 NEEDS_REVIEW，S4 继续正常流程 |
| 实现顺序调整 | 标记受影响 unit，S4 验证顺序按新顺序执行 |
| 涉及 ≤3 个 item 的细节 | 标记 item 为 NEEDS_REVIEW，S4 增量重验 |

---

## TW3: 执行微调

```
触发：TW2 完成
行为：修改 Plan 文件
```

### 执行步骤

1. **修改 Plan 文件**：编辑 `docs/plans/{feature}/ch-*/unit-*-impl.md`
2. **追加 QGW-VERSION 标记**：
   ```html
   <!-- QGW-VERSION: vX.Y | timestamp | reason: 微调原因 | type: plan-tweak -->
   ```
3. **更新 Plan frontmatter**：递增 patch 版本号

### QGW-VERSION 标记规则

- 必须追加到修改的 Plan 文件中
- `type: plan-tweak` 区分于正常 Plan 修订
- 标记是 compaction 恢复和 `--self` 复盘的基础

---

## TW4: 标记受影响项

```
触发：TW3 完成
行为：标记 verification JSON 中受影响的 item
```

### 标记规则

1. **item 状态标记**：受影响的 item `status` 保持当前值不变，追加 `needs_review: true` 字段
2. **S4 verifier 提示**：S4 执行时检查 `needs_review` 标记，对受影响项额外输出验证结果
3. **Session Summary 记录**：在 Decisions 表中记录微调事件

### 与 `--prd-changed` 的区别

| 维度 | Plan 微调 (`--plan-tweak`) | PRD 变更 (`--prd-changed`) |
|------|--------------------------|--------------------------|
| 触发场景 | Plan 实现细节调整 | PRD 源需求变更 |
| 可验证项 | 不改定义 | 可能改定义 |
| 引擎行为 | 记录 tweak，步骤状态不变 | 按 impact 级别重置步骤 |
| Gate 影响 | 不重跑 Gate | minor/major 需增量/全量重跑 |
| 版本标记 | QGW-VERSION type=plan-tweak | QGW-VERSION type=prd-change |
