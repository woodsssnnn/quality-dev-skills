# Scenario 1: 参数解析准确性

## 目的

验证 skill 在不同参数组合下是否正确路由到对应的 Gate / 模式，以及无参数输入是否被正确忽略。

## 场景

### 1.1 用户使用 `--gate1`

**trigger_input**: "根据PRD写这个需求的计划 --gate1"

**expected_behavior**:
- [ ] 识别为 Gate 1 触发（`--gate1` 参数）
- [ ] 默认选择 PRD 模式（无 `--bug`/`--opt` 时）
- [ ] 输出 `[qgw:gate1] 启动 PRD 模式`
- [ ] 进入 P1 流程（解析需求 → 提取可验证项）

### 1.2 用户使用 `--gate2 --debug`

**trigger_input**: "修一下这个bug --gate2 --debug"

**expected_behavior**:
- [ ] 识别为 Gate 2 触发（`--gate2` 参数）
- [ ] 选择 Debug 模式（`--debug` 参数）
- [ ] 输出 `[qgw:debug] 启动`
- [ ] 进入 D1 流程（定义修复标准）

### 1.3 用户使用 `--gate2 --audit`

**trigger_input**: "对照PRD审计流程穿透模块 --gate2 --audit"

**expected_behavior**:
- [ ] 识别为 Gate 2 触发（`--gate2` 参数）
- [ ] 选择 Audit 模式（`--audit` 参数）
- [ ] 输出 `[qgw:audit] 启动`
- [ ] 进入 Audit A 流程（分解 unit）

### 1.4 用户使用 `--all --strict`

**trigger_input**: "全流程检查这个需求 --all --strict"

**expected_behavior**:
- [ ] 识别为全流程触发（`--all` 参数）
- [ ] `--strict` 修饰：零偏差放行
- [ ] 先执行 Gate 1 PRD 模式，完成后进入 Gate 2 Implementation 模式
- [ ] 输出 `[qgw:gate1] 启动 PRD 模式 (strict)`

### 1.5 用户不使用任何参数

**trigger_input**: "实现这个功能"

**expected_behavior**:
- [ ] 不触发 quality-gate-workflow skill
- [ ] 不输出任何 `[qgw:...]` 格式的日志
- [ ] 不进入 Gate 1 或 Gate 2 任何模式
- [ ] 按普通开发请求处理

### 1.6 用户使用 `--gate1 --bug`

**trigger_input**: "分析这个bug的根因 --gate1 --bug"

**expected_behavior**:
- [ ] 识别为 Gate 1 触发（`--gate1` 参数）
- [ ] 选择 Bug 模式（`--bug` 参数）
- [ ] 输出 `[qgw:gate1] 启动 Bug 模式`
- [ ] 进入 P1-Bug 流程（提取 bug 症状 + 根因假设）

## 评估标准

| 编号 | 检查项 | 权重 |
|------|--------|------|
| T1.1 | `--gate1` → Gate 1 PRD 模式 | 必须 |
| T1.2 | `--gate2 --debug` → Gate 2 Debug 模式 | 必须 |
| T1.3 | `--gate2 --audit` → Gate 2 Audit 模式 | 必须 |
| T1.4 | `--all --strict` → 全流程 strict | 必须 |
| T1.5 | 无参数 → 不触发 | 必须 |
| T1.6 | `--gate1 --bug` → Gate 1 Bug 模式 | 必须 |

**通过条件**：全部 6 个检查项 PASS。
