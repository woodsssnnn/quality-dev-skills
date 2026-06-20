# 引擎交互协议

> 所有步骤的引擎交互统一在此文档定义。各 workflow 文档引用本协议。

---

## 核心规则

每个步骤的引擎交互遵循以下模式：

```
开始前: python gate-enforcer.py enter <step>  → ALLOW / SKIP / BLOCK
执行中: [语义工作...]
完成后: python gate-enforcer.py complete <step> → OK / BLOCK
```

**例外**：auto-complete 步骤（见下表）只需一次 `enter` 调用。

---

## 自动完成步骤

以下纯机械步骤在 `enter` 时自动执行 guard check 并 complete：

| 步骤 | 说明 | guard check |
|------|------|------------|
| P0 | 工作空间目录检查 | dirs_exist |
| S0 | 工作空间目录检查 | dirs_exist |
| P1-check | 虚拟聚合步骤 | sub_decision_checks |

**用法**：`python gate-enforcer.py enter P0` → 输出 `OK, auto_completed=true`

---

## 手动步骤

非 auto-complete 步骤需要显式 enter + complete：

```bash
python gate-enforcer.py enter P1       # → ALLOW
# ... 执行 P1 语义工作 ...
python gate-enforcer.py complete P1    # → OK, next_step=P1.5
```

---

## Bug 阻塞

P0 优先级 item FAIL 时，低优先级步骤自动 BLOCK：

```
python gate-enforcer.py enter S2
→ BLOCK: P0 优先级存在未修复的 FAIL: U1-01，低优先级步骤暂停
```

---

## 进度可视化

`status` 命令自动包含文本进度条：

```
python gate-enforcer.py status
→ Gate 1 [████████░░░░] 60% (6/11)
    ✅P0 ✅P1 ⏭P1.5 ⏭P1.6 ⏭P1.7 ✅P1-chk 🔄P2 ○P2.5 ○P3 ○P4 ○P5
    当前: P2 | 反馈: 0/2 | ses_20260620T143022
```

---

## Knowledge Compounding

P5/S5 complete 时自动触发 evolve 检查。用户无需手动调用。

---

## Gate 1 步骤引擎交互速查

| 步骤 | 模式 | guard checks |
|------|------|-------------|
| P0 | auto | dirs_exist |
| P1 | manual | — |
| P1.5 | manual | — (skippable) |
| P1.6 | manual | — (skippable) |
| P1.7 | manual | — (skippable) |
| P1-check | auto | sub_decision_checks |
| P2 | manual | plan_scope_declared |
| P2.5 | manual | plan_files_exist (skippable) |
| P3 | manual | plan_coverage |
| P4 | manual | verifier_report_written |
| P5 | manual | verification_json_valid + index + session + schema |
| P5-evolve | manual | — (skippable, auto-triggered by P5) |

## Gate 2 步骤引擎交互速查

| 步骤 | 模式 | guard checks |
|------|------|-------------|
| S0 | auto | dirs_exist |
| S1 | manual | — |
| S2 | manual | — |
| S2.5 | manual | boundary_valid |
| S3 | manual | self_verify_documented |
| S3.5 | manual | db_schema_verified (skippable) |
| S4 | manual | verifier_report_written |
| S4.5 | manual | — (skippable) |
| S5 | manual | toolcallid + coderefs + plan + feedback + schema |
| S5-evolve | manual | — (skippable, auto-triggered by S5) |
