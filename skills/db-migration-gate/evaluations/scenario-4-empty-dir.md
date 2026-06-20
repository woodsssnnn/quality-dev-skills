# Scenario 4: 空迁移目录

## 触发条件

用户执行 `--db-migration` 并指向一个空的迁移目录。

## 输入

```
--db-migration ./migrations/
```

目录 `migrations/` 存在但不含任何 `.sql` 或 `.py` 文件。

## 期望行为

- `check-migration-safety.py` 输出 "No migration files found."
- 退出码为 0（正常退出）
- 不输出任何 `[ERROR]` 行

## 验证标准

- [x] 退出码为 0
- [x] 输出包含 "No migration files found"
- [x] 无 ERROR 级别输出
