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
