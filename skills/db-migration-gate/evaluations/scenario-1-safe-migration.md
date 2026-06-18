# Scenario 1: 安全迁移通过检查

## 触发条件

用户执行 `--db-migration` 并提供合规的迁移文件。

## 输入

迁移目录包含以下文件：

`20260618_1030_add_email_to_users.py`:
```python
def upgrade():
    op.add_column('users', sa.Column('email', sa.String(255), nullable=True))
    op.create_index('idx_users_email', 'users', ['email'])

def downgrade():
    op.drop_index('idx_users_email')
    op.drop_column('users', 'email')
```

## 期望行为

- `check-migration-safety.py` 退出码为 0 (PASS)
- 文件名包含时间戳
- 有 downgrade 函数
- 索引命名符合 `idx_{table}_{column}`
- 新增列 nullable=True

## 验证标准

- [x] 文件名格式正确
- [x] down 脚本存在
- [x] 索引命名合规
- [x] 新增列允许 NULL
- [x] 无危险操作
