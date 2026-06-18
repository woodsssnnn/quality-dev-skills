# Scenario 3: Gate 2 流程遵循

## 目的

验证 Gate 2 是否严格按 Step 1→5 流程执行，验证标准是否被正确提取和逐条验证。

## 前置条件

- 已完成 Gate 1，存在 Plan 文档 + 验收清单
- 已加载 quality-gate-workflow skill
- 已加载项目的 dev_rule_path 或 gate_dev_rules 配置

## 模拟 Plan

以下是一段模拟 Plan + 验收清单，用于触发 Gate 2 Implementation 模式：

```
## Plan: 任务列表筛选器

### Unit 1: 筛选区域

#### What
实现页面顶部 4 个筛选条件 + 查询/重置按钮。

#### Where
- `frontend-webapp/custom/pages/task-list/index.tsx`
- `frontend-webapp/custom/pages/task-list/components/TaskFilter.tsx`

#### How
- 使用 antd Form + 行内布局
- 流程名称: Input
- 责任部门: TreeSelect (单选)
- 任务状态: Select，options = 待处理/进行中/已完成/已关闭，defaultValue="待处理"
- 创建时间: DatePicker.RangePicker

### Unit 2: 数据表格

#### What
实现 5 列表格，含 Tag 颜色映射和分页。

#### Where
- `frontend-webapp/custom/pages/task-list/index.tsx`
- `frontend-webapp/custom/pages/task-list/components/TaskTable.tsx`

#### How
- 使用 antd Table，columns 定义 5 列
- 任务状态列 render Tag，颜色映射：待处理=blue/进行中=orange/已完成=green/已关闭=gray
- 分页: pageSize=20

<!-- Appended by quality-gate-workflow Gate 1 -->
## Acceptance Criteria Checklist
Source: PRD-任务列表筛选器
Generated: 2026-06-09
Version: 1.1

### Unit 1: 筛选区域
- [ ] Item 1 (§6.1): 流程名称=文本输入框，支持模糊匹配
- [ ] Item 2 (§6.1): 责任部门=树选择器，单选
- [ ] Item 3 (§6.1): 任务状态=下拉框，选项=待处理/进行中/已完成/已关闭，默认"待处理"
- [ ] Item 4 (§6.1): 创建时间=日期范围选择器
- [ ] Item 5 (§6.3): 查询按钮触发筛选
- [ ] Item 6 (§6.3): 重置按钮清空所有筛选条件，恢复默认（任务状态="待处理"）

### Unit 2: 数据表格
- [ ] Item 7 (§6.2): 流程名称=文本+超链接，点击跳转流程详情
- [ ] Item 8 (§6.2): 责任人=文本，显示姓名
- [ ] Item 9 (§6.2): 责任部门=文本，显示部门全称
- [ ] Item 10 (§6.2): 任务状态=Tag，颜色映射：待处理=blue/进行中=orange/已完成=green/已关闭=gray
- [ ] Item 11 (§6.2): 创建时间=日期，YYYY-MM-DD 格式
- [ ] Item 12 (§6.3): 分页，每页 20 条
```

**trigger_input**: "按 Plan 实现任务列表筛选器 Unit 1"

## 预期行为

### Step 1: 提取验收标准

- [ ] 输出 `[qgw:gate2:S1] 提取验收标准 (来自 Gate 1 清单)`
- [ ] 从 Plan 文档的验收清单读取 Item 1-6（Unit 1 的标准）
- [ ] 不重新从 PRD 提取（直接使用 Gate 1 产物）
- [ ] 如有 dev_rule_path 或 gate_dev_rules，附加 Dev Rule Checklist
- [ ] 输出 `[qgw:gate2:S1] ✅ 6 条标准`

### Step 2: 实现

- [ ] 输出 `[qgw:gate2:S2] 实现 Unit 1/2: 筛选区域 ...`
- [ ] 按 Item 1-6 逐条实现代码
- [ ] 如有 dev_rule_path 或 gate_dev_rules 且 Plan 指定了 pattern，按 pattern 骨架实现
- [ ] 实现完成后进入 Step 3

### Step 3: 自验

- [ ] 输出 `[qgw:gate2:S3] 自验 ...`
- [ ] 逐条检查 Item 1-6：Pass / Fail + 证据
- [ ] 如有 Fail 则修复后重新检查
- [ ] 输出 `[qgw:gate2:S3] ✅ 全部通过`

### Step 4: 独立 verifier 子代理

- [ ] 输出 `[qgw:gate2:S4] 派独立 verifier 子代理 (round 1)`
- [ ] 实际调用 `Task` 或 `Agent` 工具（非仅输出日志文本）
- [ ] 子代理 prompt 包含：验收标准、源需求位置、实现代码位置、逐项 PASS/FAIL 指令
- [ ] 子代理在独立 context 中运行
- [ ] toolCallId 写入验收清单 JSON（非空字符串）
- [ ] toolCalls 数组追加 `{ step: "S4", toolCallId: "...", ... }` 记录
- [ ] 输出 `[qgw:gate2:S4] ✅ 全部 PASS` 或修复后重验

### Step 5: 100% 通过 → 提交

- [ ] 进入 S5 前检查：S4 确实产生了 Task/Agent 工具调用
- [ ] 检查验收清单 JSON 所有 item 的 toolCallId 非空
- [ ] 输出 `[qgw:gate2:S5] ✅ Unit 1/2 提交`
- [ ] 验证结果写入 `docs/verification/unit-1.json`
- [ ] evolve 状态检查（有/无新增 pattern）

## 评估标准

| 编号 | 检查项 | 权重 |
|------|--------|------|
| G2-1 | S1 从 Gate 1 验收清单读取（非重新提取） | 必须 |
| G2-2 | S2 按验收标准逐条实现 | 必须 |
| G2-3 | S3 逐条自验 PASS/FAIL（非笼统通过） | 必须 |
| G2-4 | S4 实际调用 Task/Agent 工具 | 必须 |
| G2-5 | S4 toolCallId 非空写入 | 必须 |
| G2-6 | S5 前置检查（工具调用存在 + toolCallId 非空） | 必须 |

**通过条件**：全部 6 个检查项 PASS。
