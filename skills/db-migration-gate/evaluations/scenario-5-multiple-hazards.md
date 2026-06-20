# Scenario 5: 多重危险操作混合

## 触发条件

用户执行 `--db-migration` 并提供包含多重违规的迁移文件。

## 输入

迁移目录含一个文件 `bad_migration.sql`：

```sql
TRUNCATE TABLE audit_logs;

DROP TABLE legacy_data;

ALTER TABLE users ADD COLUMN new_field VARCHAR(255) NOT NULL;

CREATE TABLE new_data (id INT);
INSERT INTO new_data SELECT id FROM legacy_data;
```

文件名：`bad_migration.sql`（无时间戳）

## 期望行为

- `check-migration-safety.py` 退出码为 1
- 检测到以下违规：
  1. 文件名缺少时间戳
  2. `TRUNCATE TABLE` 被禁止
  3. `DROP TABLE` 无 CONFIRM 标记
  4. `ADD COLUMN ... NOT NULL` 无 DEFAULT
  5. DDL + DML 混合（CREATE TABLE + INSERT INTO）
  6. 无 down/rollback 脚本

## 验证标准

- [x] 退出码为 1
- [x] 至少检测到 4 个 ERROR
- [x] TRUNCATE 被标识
- [x] DROP TABLE 无 CONFIRM 被标识
- [x] DDL+DML 混合被标识
- [x] 文件名违规被标识
