# Scenario 3: 数据回填与 Schema 变更混合

## 触发条件

用户执行 `--db-migration` 并提供同时包含 DDL 和 DML 的迁移文件。

## 输入

`20260618_1500_add_status_and_backfill.py`:
```python
def upgrade():
    # Add new column
    op.add_column('orders', sa.Column('status', sa.String(20), nullable=True, server_default='pending'))

    # Backfill existing rows
    op.execute("UPDATE orders SET status = 'completed' WHERE created_at < '2026-01-01'")

    # Create index
    op.create_index('my_custom_idx', 'orders', ['status'])

def downgrade():
    op.drop_index('my_custom_idx')
    op.drop_column('orders', 'status')
```

## 期望行为

- `check-migration-safety.py` 退出码为 1 (FAIL)
- 检测出以下问题：
  - DDL (ADD COLUMN) 和 DML (UPDATE) 混合在同一迁移 (ERROR)
  - 索引名 `my_custom_idx` 不符合 `idx_orders_status` 约定 (WARN)

## 验证标准

- [x] DDL+DML 混合被检测
- [x] 索引命名违规被检测
- [x] 退出码为 1（因 ERROR 级别问题）
- [x] 正确建议拆分为两个迁移文件
