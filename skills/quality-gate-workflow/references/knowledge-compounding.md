# Knowledge Compounding（自进化机制）

> 本文档由 SKILL.md 路由按需加载（Unit 完成后）。
> 定义 knowledge 在 error-patterns / dev-rule / advisor-templates 之间的流动规则。

---

## 1. 层级结构

| 层级 | 位置 | 写入规则 |
|------|------|---------|
| **工作空间层** | `docs/verification/error-patterns.json` | verifier 发现新 FAIL/PARTIAL 模式后自动提取 |
| **项目层** | `.agents/skills/project-dev-rule/SKILL.md` | Gate 1 P5-evolve / Gate 2 S5-evolve 自动沉淀 |
| **全局层** | `references/error-patterns.json` | 仅人工 promote（≥3 工作空间 + 用户确认） |

## 2. 阈值升级规则

工作空间层模式累计达阈值时，升级到更高层级：

| frequency | 升级目标 |
|-----------|---------|
| ≥ 3 | 升级到项目 `dev_rule.path`（项目级开发规范） |
| ≥ 5 | 升级到 `gate_dev_rules`（Gate 配置） |
| ≥ 8 | 升级到 Red Lines / 合理化借口表 |

## 3. Promote 流程

1. **自动检测**：evolve 检查每个 Unit 完成后执行，统计 frequency
2. **阈值触发**：达到阈值时输出升级建议
3. **人工确认**：必须用户确认后执行 promote
4. **全局 promote**：≥3 工作空间 + 用户确认后升级到 `references/error-patterns.json`

## 4. 完整闭环图

```
error-patterns.json (工作空间层)
    │
    │ frequency ≥ 3
    ▼
project-dev-rule / SKILL.md (项目层)
    │                               ▲
    │ 核心规则/反模式              │ Gate 1 P5-evolve
    │                               │ Gate 2 S5-evolve
    ▼                               │
advisor-templates.md               │
    │                               │
    │ {{变量}} 注入                │
    ▼                               │
顾问子代理 (PM/架构师)          │
    │                               │
    │ ISSUE 被接受                │
    └───────────────────────────────┘
```

**闭环说明**：
1. Gate 2 S4 verifier 发现 FAIL → 写入 error-patterns.json
2. S5-evolve 检查 error-patterns frequency → 达阈值升级到 project-dev-rule
3. project-dev-rule 的核心规则通过 `{{DEV_RULE_SUMMARY}}` 注入顾问 prompt
4. 顾问基于项目规范评议 → 被接受的 ISSUE 在下次 P5-evolve/S5-evolve 沉淀回 project-dev-rule

## 5. P5-evolve 执行规则

Gate 1 P5 完成后执行。详见 `gate1-workflow.md` "P5-evolve" 章节。

**输入**：
- P1 可验证项（业务术语提取）
- P1.7 PM 顾问报告（被接受 ISSUE）
- P2.5 架构师顾问报告（被接受 ISSUE + 根因簇）
- `_clarifications.md`（澄清结论）

**输出**：
- 新增 CR / AP / 术语条目到 `dev_rule.path`/SKILL.md
- 进化日志追加记录
- `evolution_count` 递增

## 6. S5-evolve 执行规则

Gate 2 S5 完成后执行。详见 `gate2-workflow.md` "S5-evolve" 章节。

**输入**：
- S4 verifier 报告（FAIL 项 + 横切检查 FAIL）
- Debug 模式 BUG 修复记录
- error-patterns.json（frequency 统计）
- P2.5 架构师 ISSUE（从 Gate 1 传递）

**输出**：
- 新增 AP 条目 / 升级 CR 到 `dev_rule.path`/SKILL.md
- 进化日志追加记录
- `evolution_count` 递增

## 7. 与 skill-optimizer 的联动

skill-optimizer 评分时可读取 project-dev-rule 的进化日志，提取高频反模式作为动态评分规则：

- AP 条目出现次数 ≥ 3 → 转化为动态评分规则（权重 0.10）
- 动态规则仅影响项目内技能评分，不影响全局 9 条静态规则

详见 `skills/skill-optimizer/references/scoring-rules.md` "动态层"章节。

## 8. 禁止事项

- ❌ 禁止自动 promote 到全局层（反模式 #17）
- ❌ 禁止跳过 evolve 检查（反模式 #19）
- ❌ 禁止在 evolve 中修改 CLAUDE.md（冲突标注在 CR 条目中即可）
- ❌ 禁止提取被驳回的 ISSUE 作为规则（只有被接受的才沉淀）
# Knowledge Compounding（自进化机制）

> 本文档由 SKILL.md 路由按需加载（Unit 完成后）。

每个 Unit 完成后执行 evolve 检查（无 FAIL 也确认"无新增 pattern"）。

## 层级结构

| 层级 | 位置 | 写入规则 |
|------|------|---------|
| **工作空间层** | `docs/verification/error-patterns.json` | verifier 发现新 FAIL/PARTIAL 模式后自动提取 |
| **全局层** | `references/error-patterns.json` | 仅人工 promote（≥3 工作空间 + 用户确认） |

## 阈值升级规则

工作空间层模式累计达阈值时，升级到更高层级：

| frequency | 升级目标 |
|-----------|---------|
| ≥ 3 | 升级到项目 `dev_rule_path`（项目级开发规范） |
| ≥ 5 | 升级到 `gate_dev_rules`（Gate 配置） |
| ≥ 8 | 升级到 Red Lines / 合理化借口表 |

## Promote 流程

1. **自动检测**：evolve 检查每个 Unit 完成后执行，统计 frequency
2. **阈值触发**：达到阈值时输出升级建议
3. **人工确认**：必须用户确认后执行 promote
4. **全局 promote**：≥3 工作空间 + 用户确认后升级到 `references/error-patterns.json`

## 禁止事项

- ❌ 禁止自动 promote 到全局层（反模式 #17）
- ❌ 禁止跳过 evolve 检查（反模式 #19）
