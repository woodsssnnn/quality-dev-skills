# Quality Gate Workflow 评估框架

## 评估目的

本目录包含 quality-gate-workflow skill 的评估场景，用于验证 skill 在不同输入下的行为是否符合预期。评估覆盖五个维度：参数解析准确性、Gate 1 流程遵循、Gate 2 流程遵循、Debug 模式最小修复、反模式阻止。

## 如何运行评估

1. 打开一个新对话，加载 quality-gate-workflow skill
2. 按评估场景文件中的 `trigger_input` 向 Claude 发送输入
3. 观察 Claude 的实际行为
4. 逐条对照 `expected_behavior` 列表，记录 PASS / FAIL
5. 汇总结果，计算通过率

### 评估频率

- 每次 skill 版本升级后必须运行全部场景
- 修改模式路由逻辑后至少运行 scenario-1
- 修改 Gate 1 工作流后至少运行 scenario-2
- 修改 Gate 2 工作流后至少运行 scenario-3
- 修改 Debug 模式后至少运行 scenario-4
- 修改红线/反模式后至少运行 scenario-5

### 结果记录格式

```
## 评估结果: [场景名称]
日期: YYYY-MM-DD
Skill 版本: vX.X
评估人: [姓名]

| # | 预期行为 | 实际行为 | 结果 |
|---|---------|---------|------|
| 1 | ... | ... | PASS/FAIL |
| 2 | ... | ... | PASS/FAIL |

通过率: N/M (XX%)
```

## 评估指标定义

### M1: 参数解析准确率 (Parameter Accuracy)

正确解析参数路由或不触发 skill 的输入占比。

- **计算**：正确路由的参数组合数 / 总输入数
- **及格线**：100%（错误路由意味着整个流程失败）
- **来源场景**：scenario-1

### M2: Gate 1 流程遵循率 (Gate 1 Adherence)

Gate 1 P1→P5 每个步骤是否按规范执行。

- **计算**：正确执行的步骤数 / 总步骤数
- **及格线**：100%（跳过任何步骤 = 需求遗漏风险）
- **来源场景**：scenario-2

### M3: Gate 2 流程遵循率 (Gate 2 Adherence)

Gate 2 Step 1→5 每个步骤是否按规范执行。

- **计算**：正确执行的步骤数 / 总步骤数
- **及格线**：100%（跳过任何步骤 = 代码偏差风险）
- **来源场景**：scenario-3

### M4: 最小修复率 (Minimal Fix Rate)

Debug 模式下修复范围是否严格限定在标准内。

- **计算**：无 over-fixing 的修复数 / 总修复数
- **及格线**：100%（一次 over-fixing = 未验证代码进入代码库）
- **来源场景**：scenario-4

### M5: 反模式阻止率 (Anti-pattern Prevention)

已知反模式被成功阻止的比例。

- **计算**：成功阻止的反模式数 / 总反模式数
- **及格线**：100%（放行一个反模式 = 质量缺口）
- **来源场景**：scenario-5

### 综合评分

综合评分 = (M1 + M2 + M3 + M4 + M5) / 5

- **优秀**：100%
- **合格**：100%（任何指标低于 100% 即为不合格）
- **不合格**：任何指标 < 100%

## 评估场景索引

| 文件 | 测试维度 | 场景数 |
|------|---------|--------|
| scenario-1-trigger-accuracy.md | 触发准确性 | 4 |
| scenario-2-gate1-adherence.md | Gate 1 流程遵循 | 5 |
| scenario-3-gate2-adherence.md | Gate 2 流程遵循 | 6 |
| scenario-4-debug-mode.md | Debug 最小修复 | 3 |
| scenario-5-anti-patterns.md | 反模式阻止 | 3 |
