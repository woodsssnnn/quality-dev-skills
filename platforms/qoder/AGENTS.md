# Quality Dev Skills — Qoder 平台

质量门禁工作流和项目开发规范技能集合（Qoder 平台适配）。

## 技能清单

| 技能 | 触发 | 说明 |
|------|------|------|
| `quality-gate-workflow` | `--gate1` / `--gate2` / `--all` | 质量门禁工作流 |
| `skill-optimizer` | `--optimize` | 技能自动优化 |
| `qgw-init` | `--init` | 项目初始化引导 |
| `api-design-review` | `--api-review` | API 设计审查 |
| `db-migration-gate` | `--db-migration` | 数据库迁移检查 |

## 使用方式

在 Qoder 中通过 skill 系统自动加载。触发参数：

```
--gate1          # 需求→Plan
--gate2          # Plan→代码
--all            # 全流程
--self           # 自检
--analyze        # 一致性分析
--prd-changed    # PRD 变更正向触发
--plan-tweak     # Plan 轻量微调
--init           # 项目初始化
--optimize       # 技能优化
--api-review     # API 审查
--db-migration   # 迁移检查
```

## 安装

```bash
git clone https://gitcode.com/songnan/quality-dev-skills.git ~/quality-dev-skills
cd ~/quality-dev-skills
bash scripts/install.sh
```

## 更多信息

- [README](../../README.md)
- [通用平台文档](../general/AGENTS.md)
