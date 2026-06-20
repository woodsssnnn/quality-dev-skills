# 网状生命周期（Multi-Path Lifecycle）

> QGW 不是线性流水线。用户可以在任意节点进入、跳转、恢复。
> 本文档定义所有入口点和跳转规则。

---

## 入口点（Entry Points）

| ID | 名称 | 你的状态 | 引擎参数 | 起始步骤 |
|----|------|---------|---------|---------|
| EP-1 | fresh-prd | 有新需求文档 | `init --gate gate1 --mode prd` | P0 |
| EP-2 | existing-plan | 已有 Plan，要实现代码 | `init --gate gate2 --mode impl` | S0 |
| EP-3a | bug-with-plan | Bug 需分析根因 | `init --gate gate1 --mode bug` | P0 |
| EP-3b | bug-direct | Bug 定位明确 | `init --gate gate2 --mode debug` | D1 |
| EP-4 | optimization | 重构/优化需求 | `init --gate gate1 --mode opt` | P0 |
| EP-5 | prd-changed | PRD 有变更 | `prd-changed --impact X` | 动态（见跳转规则） |
| EP-6 | plan-tweak | Gate 2 中微调 Plan | `plan-tweak --reason X` | 当前步骤不变 |
| EP-7 | resume | 上次会话中断 | `resume` | 上次中断点 |
| EP-8 | audit | 审计已有代码 | `init --gate audit` | A |
| EP-9 | self-review | 复盘会话质量 | `self-check` | SC0 |
| EP-10 | evolve | 学习反模式 | `complete P5/S5` 自动触发 | P5-evolve/S5-evolve |

**核心原则**：用户只需 `init` → `enter` → `complete`，引擎内部自动处理排序、进化、降噪、跳转。

---

## 跳转规则（Transition Rules）

| ID | 源状态 | 触发条件 | 目标 | 引擎行为 |
|----|-------|---------|------|---------|
| TR-1 | Gate 2 运行中 | verifier FAIL + rootCause=PLAN | Gate 1 P2（修 Plan） | `fail S4 --rootCause PLAN` → 自动重置 P2 为 NOT_STARTED |
| TR-2 | Gate 2 运行中 | verifier FAIL + rootCause=CODE | Gate 2 S2（修代码） | `fail S4 --rootCause CODE` → 自动重置 S2 为 NOT_STARTED |
| TR-3 | self-review | Plan 质量问题 | Gate 1 P3 | 用户手动 `init --gate gate1` 重新进入 |
| TR-4 | self-review | 发现可学习反模式 | Knowledge evolve | `complete P5/S5` 自动触发 evolve |
| TR-5 | Gate 2 运行中 | PRD minor 变更 | S4 增量重验 | `prd-changed --impact minor` → 重置 S4 |
| TR-6 | Gate 2 运行中 | PRD major 变更 | Gate 1 全量 | `prd-changed --impact major` → 重置 S1~S4 |
| TR-7 | evolve 完成 | 规则文件已更新 | 影响下次 Gate 1/2 | 无引擎动作（规则文件自动生效） |
| TR-8 | Gate 2 bug | Bug 根因在 Plan | Gate 1 bug 模式 | 用户手动 `init --gate gate1 --mode bug` |
| TR-9 | 任意 | 会话中断/compaction | 上次断点恢复 | `resume` 自动恢复 RUNNING→NOT_STARTED |

---

## 状态转换图

```
                          ┌────────────┐
                          │  EP-9      │
                          │ self-check │
                          └─────┬──────┘
                                │ TR-3 (Plan问题)  TR-4 (反模式学习)
                   ┌────────────┼────────────┐
                   ▼            ▼            ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐
             │  Gate 1  │ │  evolve  │ │  Gate 2  │
             │  P0→P5   │ │ P5/S5    │ │  S0→S5   │
             │ +evolve  │ │ (自动)    │ │ +evolve  │
             └────┬─────┘ └──────────┘ └────┬─────┘
                  │                          │
          ┌───────┼───────┐          ┌───────┼───────┐
          ▼       ▼       ▼          ▼       ▼       ▼
       EP-1    EP-3a   EP-4       EP-2    EP-3b   EP-8
      fresh    bug     opt       exist    bug    audit
       prd    +plan    mode       plan   direct   mode
                  │                       │
                  │ TR-1 (PLAN root)      │
                  │◄──────────────────────┘
                  │ TR-2 (CODE root)
                  │──────────────────────► (back to S2)

       EP-5 (prd-changed)
       ├── cosmetic → 标记 NEEDS_REVIEW（不跳转）
       ├── minor → TR-5（重置 S4 增量重验）
       └── major → TR-6（重置 S1~S4 全量重跑）

       EP-6 (plan-tweak) → 当前步骤不变，记录微调

       EP-7 (resume) → 任意断点恢复

       EP-10 (evolve) → 自动嵌入 P5/S5 complete
```

---

## 优先级与阻塞

Plan Unit 支持 P0/P1/P2 优先级。Gate 2 按优先级排序执行。

**Bug 阻塞传播**：
- P0 item FAIL → P1/P2 步骤暂停（引擎自动 BLOCK）
- P0 修复后 → P1/P2 自动恢复
- P1 FAIL 不阻塞 P2

```
Gate 2 执行顺序:
  S0 → [P0 units] → [P1 units] → [P2 units] → S4 → S5

Bug 阻塞:
  P0-01 FAIL ──BLOCK──► P1 步骤暂停
  P0-01 修复 ──恢复──► P1 步骤继续
```

---

## 入口点使用示例

### EP-1: 全新需求

```bash
python gate-enforcer.py init --gate gate1 --mode prd
python gate-enforcer.py enter P0     # 自动 complete（目录检查）
python gate-enforcer.py enter P1     # 手动：解析需求
python gate-enforcer.py complete P1
# ... 继续 P2→P5
# P5 complete 后自动触发 evolve
```

### EP-2: 已有 Plan，实现代码

```bash
python gate-enforcer.py init --gate gate2 --mode impl
python gate-enforcer.py enter S0     # 自动 complete
python gate-enforcer.py enter S1     # 手动：读取 Plan
# Gate 2 按优先级排序：先 P0 units，再 P1，再 P2
```

### EP-3b: 快速修 Bug

```bash
python gate-enforcer.py init --gate gate2 --mode debug
python gate-enforcer.py enter D1     # 定义修复标准
python gate-enforcer.py enter D2     # 修复
python gate-enforcer.py enter D3     # 自验
python gate-enforcer.py enter D4     # verifier
```

### EP-5: PRD 变更

```bash
# 在 Gate 2 运行中发现 PRD 有变更
python gate-enforcer.py prd-changed --impact minor --scope §2.3
# 引擎自动重置 S4，建议增量重验
```

### EP-7: 恢复中断会话

```bash
python gate-enforcer.py resume
# 引擎回答：上次在 P2 中断，下一步是 P2.5
```

### EP-10: evolve（自动）

```bash
# 用户无需手动调用
# complete P5 时引擎自动：
# 1. 提取 verifier FAIL/PARTIAL 模式
# 2. 去重后写入 error-patterns.json
# 3. 检查阈值，输出升级建议
```

---

## 跳转时的状态保护

| 规则 | 说明 |
|------|------|
| 已完成步骤不丢失 | TR-1 重置 P2 时，P0/P1/P1-check 保持 COMPLETED |
| 反馈轮次累计 | 跨 Gate 跳转时 feedback_rounds 持续计数 |
| Skip 矩阵不可变 | init 时确定的 skip 矩阵在跳转后保持不变 |
| evolve 日志追加 | 每次 evolve 执行记录追加到 evolution-log.json，不覆盖 |
