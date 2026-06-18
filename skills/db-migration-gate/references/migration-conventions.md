# 数据库迁移约定

数据库 schema 变更的安全规范和命名约定。

## 文件命名

### Alembic 风格（Python）

```
20260618_1030_add_user_email_index.py
20260618_1200_create_orders_table.py
```

格式：`{YYYYMMDD}_{HHMM}_{description}.py`

### Flyway 风格（SQL）

```
V202606181030__add_user_email_index.sql
V202606181200__create_orders_table.sql
```

格式：`V{YYYYMMDDHHMM}__{description}.sql`

### 规则

- 时间戳精确到分钟，确保顺序唯一
- description 使用 snake_case，描述变更内容
- 禁止手动修改文件名中的时间戳

## 安全规则

### 禁止操作（除非有确认标记）

- `DROP TABLE` — 必须添加 `-- CONFIRM: DROP TABLE table_name`
- `DROP COLUMN` — 必须添加 `-- CONFIRM: DROP COLUMN table.column`
- `TRUNCATE TABLE` — 禁止在迁移中出现
- `RENAME TABLE` — 使用 add-new → migrate-data → drop-old 三步法

### 大表操作（> 100 万行）

- ALTER TABLE 必须分批执行（每批 1000-10000 行）
- 创建索引使用 `CONCURRENTLY`（PostgreSQL）或 `ALGORITHM=INPLACE`（MySQL）
- 数据回填必须单独迁移文件，不与 schema 变更混在一起

### 向后兼容

- 新增列必须有 DEFAULT 值或允许 NULL
- 删除列分两步：先停止代码引用 → 下个版本再 DROP
- 重命名列分三步：add new → copy data → drop old

## Down 脚本要求

- 每个 up 迁移必须有对应的 down 迁移
- down 必须能将 schema 恢复到迁移前状态
- DROP 操作的 down 是 CREATE + 数据恢复方案
- 如果数据无法恢复，必须在 down 中标注 `-- IRREVERSIBLE`

## 索引命名

| 类型 | 格式 | 示例 |
|------|------|------|
| 普通索引 | `idx_{table}_{column}` | `idx_users_email` |
| 唯一索引 | `uniq_{table}_{column}` | `uniq_users_username` |
| 外键 | `fk_{table}_{ref_table}` | `fk_orders_users` |
| 主键 | `pk_{table}` | `pk_users` |
| 检查约束 | `ck_{table}_{column}` | `ck_users_age_positive` |

## Review 检查清单

- [ ] 迁移文件名包含时间戳
- [ ] 有 down 脚本
- [ ] DROP 操作有 CONFIRM 标记
- [ ] 大表操作分批执行
- [ ] 新增列有 DEFAULT 或 NULL
- [ ] 索引命名符合约定
- [ ] 无数据回填与 schema 变更混合
