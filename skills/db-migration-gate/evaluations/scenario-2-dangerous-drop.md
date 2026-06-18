# Scenario 2: 危险 DROP 操作被拦截

## 触发条件

用户执行 `--db-migration` 并提供包含未确认 DROP 操作的迁移文件。

## 输入

`rename_users_table.sql`:
```sql
-- Rename users to accounts
DROP TABLE users;
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255)
);
```

## 期望行为

- `check-migration-safety.py` 退出码为 1 (FAIL)
- 检测出以下问题：
  - 文件名缺少时间戳 (ERROR)
  - DROP TABLE 无 CONFIRM 标记 (ERROR)
  - 无 down 脚本 (ERROR)

## 验证标准

- [x] 缺少时间戳被检测
- [x] 未确认的 DROP TABLE 被检测
- [x] 无 down 脚本被检测
- [x] 退出码为 1
