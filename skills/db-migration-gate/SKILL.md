---
name: db-migration-gate
category: vertical
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
description: "Use when reviewing database migration files for safety and convention compliance. Triggers on: --db-migration, migration review."
triggers:
  parameters:
    - --db-migration
  keywords:
    - migration review
    - db migration
    - schema change
    - alembic
    - flyway
metadata:
  version: 0.8.0.1
integration:
  extends:
    - quality-gate-workflow
  extended_by: []
  shares_artifacts_with:
    - quality-gate-workflow
---

# 数据库迁移门禁

检查数据库迁移文件是否符合安全规范和团队约定，防止危险 schema 变更进入生产环境。

## 核心原则

1. **安全优先** — 禁止无回滚方案的破坏性变更
2. **向后兼容** — 迁移必须可安全地与旧代码并行运行
3. **可逆性** — 每个迁移必须有对应的 down 脚本

## 何时使用

- 提交数据库迁移文件时
- Code Review 中涉及 schema 变更
- 发布前检查迁移文件安全性

## 快速参考

| 场景 | 做法 |
|------|------|
| 新增迁移文件 | 运行 `python scripts/check-migration-safety.py <migration-dir>` |
| Review PR | 检查变更的迁移文件 |
| 发布前 | 全量扫描迁移目录 |

## 检查项

| # | 检查项 | 严重度 |
|---|--------|--------|
| 1 | DROP TABLE/COLUMN 需要确认标记 | ERROR |
| 2 | 迁移文件必须有 down 脚本 | ERROR |
| 3 | 大表 ALTER 需要分批执行 | WARN |
| 4 | 索引命名遵循 `idx_{table}_{column}` 格式 | WARN |
| 5 | 禁止在迁移中包含数据回填（大表） | ERROR |
| 6 | 迁移文件命名包含时间戳 | ERROR |

## 参考

- [迁移约定](references/migration-conventions.md)
- [垂直技能开发指南](../../shared/vertical-skill-guide.md)
