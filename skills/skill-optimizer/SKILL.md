---
name: skill-optimizer
description: "按最佳实践规则优化已有技能的质量。通过 rollout → score → bounded edit → gate 循环持续提升技能 SKILL.md 的合规度与可用性。Triggers on: --optimize, 优化技能, 优化skill, skill质量, skill评分, optimize skill."
allowed-tools:
  - Task
  - Agent
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
metadata:
  version: 0.7.0.0
---

# Skill Optimizer

基于 SkillOpt 方法论的技能自动优化框架。通过 rollout → score → bounded edit → gate 循环，持续提升技能质量。

## 快速开始

**做什么**：按最佳实践规则优化已有技能质量（rollout → score → bounded edit → gate 循环）
**怎么触发**：
- 参数式（推荐）：`--optimize <skill-path>`
- 关键词："优化技能""优化 skill""skill 评分""skill 质量"
**前置条件**：Python 3（运行 `scripts/evaluate.py` 打分）+ 一个待优化的目标技能
**第一次用**：用 `--optimize skills/<skill-name>` 指定优化目标，工具会读取该技能的 SKILL.md 并按 `references/scoring-rules.md` 打分、迭代优化

## 核心原则

1. **Bounded Edit** — 只改文本内容，不改目录结构、不改文件名、不增删文件
2. **Score-Gated** — 每轮优化必须在 val set 上分数提升才接受，否则回滚
3. **Rule-Based** — 优化目标是 best-practices 合规度，不是 benchmark 表现

## 何时使用

- 技能质量评分低于预期，需要系统性优化
- 新建技能后想验证是否符合 best-practices
- 技能迭代后想确认没有引入反模式

## 优化流程

### Step 1: 分析目标技能

```
读取目标 SKILL.md + references/
提取: description、目录结构、规则列表、检查清单
输出: 技能结构摘要
```

### Step 2: 生成评估基准

```
从 scoring-rules.md 加载 9 条规则
从目标技能生成 test cases（用户输入 → 期望行为）
划分 train/val 集（80/20）
```

### Step 3: 基线测试（Red）

```
用 subagent 在无 skill 情况下执行 test cases
记录违规、合理化借口
计算 baseline score
```

### Step 4: 优化循环

```
MAX_EPOCHS = 5
for epoch in range(MAX_EPOCHS):
    a. Rollout: subagent 用当前 skill 执行 train cases
    b. Score: evaluate.py 打分
    c. Reflect: 分析失败轨迹，生成 edit 候选
    d. Apply: 应用 bounded edit（只改文本，不改结构）
    e. Gate: 在 val cases 上验证
    f. if val_score > baseline → 接受，否则回滚
    
    if no edit improved → break
```

### Step 5: 最终验证（TDD 绿）

```
用压力场景测试优化后的 skill
确认通过
```

### Step 6: 输出

```
optimized/SKILL.md     — 优化后的技能文件
eval/report.md         — 每轮 score 对比
```

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--optimize <skill-path>` | 优化指定技能（推荐触发方式） | — |
| `--target <skill-path>` | 目标技能路径（同 --optimize） | 必填 |
| `--max-epochs <n>` | 最大优化轮数 | 5 |
| `--train-ratio <n>` | 训练集比例 | 0.8 |
| `--output <dir>` | 输出目录 | `./optimized` |

> `--optimize` 和 `--target` 等价，两者皆可触发。关键词触发作为 fallback。

## 快速参考

| 场景 | 做法 |
|------|------|
| 优化单个技能 | `--target skills/quality-gate-workflow` |
| 只评估不优化 | 运行 Step 1-3，跳过 Step 4 |
| 自定义规则 | 编辑 `references/scoring-rules.md` |

## 目录结构

```
skill-optimizer/
├── SKILL.md                    ← 主入口（本文件）
├── references/
│   ├── scoring-rules.md        ← 9 条评分规则
│   ├── optimization-algorithm.md ← 优化循环伪代码
│   └── anti-patterns.md        ← 常见优化陷阱
├── scripts/
│   └── evaluate.py             ← 评估器脚本
├── eval/
│   └── test-cases/
│       └── template.md         ← 测试用例模板
└── CHANGELOG.md
```

## 参考

- [评分规则](references/scoring-rules.md)
- [优化算法](references/optimization-algorithm.md)
- [反模式](references/anti-patterns.md)
