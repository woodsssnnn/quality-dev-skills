# Scenario 6: PRD 变更正向触发流程

## 触发条件

用户在 Gate 2 执行中声明 PRD 有变更，覆盖 cosmetic/minor/major 三级。

## 输入

### 场景 6a: cosmetic 级别

```bash
python gate-enforcer.py prd-changed --impact cosmetic --scope §3.1
```

### 场景 6b: minor 级别（S4 已 COMPLETED）

```bash
python gate-enforcer.py prd-changed --impact minor --scope §2.3
```

### 场景 6c: major 级别

```bash
python gate-enforcer.py prd-changed --impact major
```

## 期望行为

**6a cosmetic**:
- 返回 OK，不重置任何步骤
- `prd_change` 记录被写入 state
- PRD Impact Report 被生成到 `docs/reports/`
- 建议：标记 Plan 受影响章节为 NEEDS_REVIEW

**6b minor**:
- 返回 OK，S4 被重置为 NOT_STARTED
- PRD Impact Report 被生成
- 建议：增量重验受影响的可验证项

**6c major**:
- 返回 OK，S1~S4.5 全部被重置为 NOT_STARTED
- PRD Impact Report 被生成
- 建议：全量重跑 Gate 1

## 验证标准

- [ ] cosmetic 不重置任何步骤
- [ ] minor 仅重置 S4
- [ ] major 重置 S1~S4.5（不含 S0、S5）
- [ ] 三种级别均生成 PRD Impact Report
- [ ] 无效级别（如 "catastrophic"）返回 BLOCK
