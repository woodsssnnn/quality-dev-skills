# Scenario 7: Plan 微调流程

## 触发条件

用户在 Gate 2 执行中（S1~S3 之间）需要对 Plan 做轻量微调。

## 输入

### 场景 7a: 正常微调（S2 RUNNING 时）

```bash
python gate-enforcer.py plan-tweak --reason "验收标准 V2.1 描述不精确" --scope ch-2.3
```

### 场景 7b: S4 之后微调（应被阻止）

在 S4 已 COMPLETED 后尝试微调：

```bash
python gate-enforcer.py plan-tweak --reason "发现遗漏" --scope ch-1.0
```

### 场景 7c: 非 Gate 2 会话微调（应被阻止）

```bash
python gate-enforcer.py plan-tweak --reason "调整" --scope ch-1.0
```

（当前 gate 为 gate1）

## 期望行为

**7a 正常微调**:
- 返回 OK，`plan_tweaks` 记录被写入 state
- tweak_count 递增
- 不重置任何步骤（微调不影响流程状态）

**7b S4 后微调**:
- 返回 BLOCK
- 提示：Plan 微调不允许在 S4 (verifier) 之后执行
- 建议使用 `--prd-changed` 替代

**7c 非 Gate 2 微调**:
- 返回 BLOCK
- 提示：Plan 微调仅适用于 Gate 2

## 验证标准

- [ ] S1~S3 之间微调正常执行
- [ ] S4 后微调被阻止并给出明确提示
- [ ] 非 Gate 2 会话微调被阻止
- [ ] 微调不重置任何步骤状态
- [ ] `plan_tweaks` 记录包含 reason、scope、timestamp
