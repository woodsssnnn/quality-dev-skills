#!/bin/bash
# verify-checkpoint.sh — 提交前验收状态检查 + 过程化状态校验（v6.0）
#
# 用途：
#   Pre-commit Hook：7 项检查确保流程完整性。
#   支持 QGW_HOOK_MODE 环境变量控制检查严格度。
#
# 配置方式：
#   自动安装：bash ~/.agents/skills/quality-gate-workflow/scripts/hook-install.sh
#   手动写入 settings.json 或 settings.local.json（Claude Code）：
#   {
#     "hooks": {
#       "PreToolUse": [{
#         "command": "bash ~/.agents/skills/quality-gate-workflow/scripts/verify-checkpoint.sh",
#         "matcher": "Bash",
#         "hooks": ["git commit"]
#       }]
#     },
#     "env": { "QGW_HOOK_MODE": "strict" }
#   }
#
# 检查逻辑（v6.0 — 7 项检查）：
#   1. Plan 文档存在性 — 有 verification 但无 plan → ❌
#   2. JSON 指向有效 Plan — plan 字段指向不存在的文件 → ❌
#   3. error-patterns 存在 — FAIL 已发生但无 error-patterns.json → ❌
#   4. QGW-INDEX.md 存在 — 有 plan/verification 但无 INDEX → ⚠️
#   5. 验收项有 source 引用 — item 无 source 字段 → ⚠️
#   6. verifierReports 非空 — 全 PASS 但无 verifier 报告 → ❌
#   7. 原有 PASS + toolCallId — 同 v5.x 逻辑 → ❌
#
# 环境变量：
#   QGW_HOOK_MODE=strict（默认）— 所有 ❌ 检查阻止提交
#   QGW_HOOK_MODE=warn — 只警告不阻止
#   QGW_HOOK_MODE=off — 跳过所有 QGW 检查
#
# 依赖：Python 3 (用于可靠的 JSON 解析)

# ===== QGW_HOOK_MODE 检查 =====
HOOK_MODE="${QGW_HOOK_MODE:-strict}"
if [ "$HOOK_MODE" = "off" ]; then
    exit 0
fi

VERIFICATION_DIR="docs/verification"
PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[quality-gate] ⚠ 未找到 Python (python3/python)，无法解析验证数据，跳过检查"
    exit 0
fi

# 计数器
BLOCK_COUNT=0
WARN_COUNT=0

block_check() {
    BLOCK_COUNT=$((BLOCK_COUNT + 1))
    if [ "$HOOK_MODE" = "warn" ]; then
        echo "[quality-gate] ⚠️  $1"
        WARN_COUNT=$((WARN_COUNT + 1))
    else
        echo "[quality-gate] ❌ $1"
    fi
}

warn_check() {
    echo "[quality-gate] ⚠️  $1"
    WARN_COUNT=$((WARN_COUNT + 1))
}

pass_check() {
    echo "[quality-gate] ✅ $1"
}

# ===== 过程化状态校验（Phase Gate Check）=====

GATE_STATE_FILE="docs/.gate-state"

# 1. 检查是否有 Plan 文档
plan_files=$(ls docs/plans/*.md 2>/dev/null | head -3)
plan_count=$(echo "$plan_files" | grep -c '.md' 2>/dev/null || echo "0")

# 2. 尝试读取状态文件
if [ -f "$GATE_STATE_FILE" ]; then
    gate_state=$(cat "$GATE_STATE_FILE" | tr -d ' \t\n\r')
    case "$gate_state" in
        plan)
            if [ "$plan_count" -eq 0 ]; then
                block_check "流程状态不一致: 状态标记为 'plan' 但 docs/plans/ 无 Plan 文件"
            fi
            ;;
        code)
            if [ -z "$(ls docs/verification/*.json 2>/dev/null)" ]; then
                block_check "流程状态不一致: 状态标记为 'code' 但 docs/verification/ 无验收数据"
            fi
            ;;
        verified)
            ;;
        *)
            echo "[quality-gate] ⚠ 状态文件 docs/.gate-state 值异常 ('$gate_state')，将重新检查"
            ;;
    esac
fi

# 3. 若 Plan 存在但无 verification 数据 — 仍在 Gate 1 阶段，无需拦截
if [ "$plan_count" -gt 0 ] && [ -z "$(ls docs/verification/*.json 2>/dev/null)" ]; then
    echo "[quality-gate] ℹ 检测到 Gate 1 Plan 阶段，Gate 2 验收数据尚未生成，跳过提交检查"
    exit 0
fi

# 查找最新的验收清单文件
latest_file=$(ls -t "$VERIFICATION_DIR"/*.json 2>/dev/null | head -1)

if [ -z "$latest_file" ]; then
    echo "[quality-gate] ⚠ 未找到验收清单 JSON (docs/verification/)，跳过检查"
    exit 0
fi

# ===== 7 项检查 =====

"$PYTHON" -c "
import json, sys, os

latest_file = '$latest_file'
plan_count = $plan_count

try:
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
except (json.JSONDecodeError, IOError) as e:
    print(f'[quality-gate] ❌ JSON 解析失败: {e}')
    sys.exit(1)

issues = []  # (level, message) — level: 'block' or 'warn'

# --- Check 1: Plan 文档存在性 ---
plan_ref = data.get('plan', '')
if plan_ref and not os.path.exists(plan_ref):
    issues.append(('block', f'Check 1 FAIL: verification JSON 引用的 Plan 不存在: {plan_ref}'))
elif plan_count == 0 and not plan_ref:
    issues.append(('block', f'Check 1 FAIL: 有 verification JSON 但 docs/plans/ 无 Plan 文件'))
else:
    print('[quality-gate] ✅ Check 1: Plan 文档存在')

# --- Check 2: JSON 指向有效 Plan ---
if plan_ref and not os.path.exists(plan_ref):
    issues.append(('block', f'Check 2 FAIL: JSON 中 plan 路径无效: {plan_ref}'))
else:
    print('[quality-gate] ✅ Check 2: JSON plan 路径有效')

# --- Check 3: error-patterns 存在 ---
has_fail = False
for unit in data.get('units', []):
    for item in unit.get('items', []):
        if item.get('status') == 'FAIL':
            has_fail = True
            break
    if has_fail:
        break

if has_fail and not os.path.exists('docs/verification/error-patterns.json'):
    issues.append(('block', f'Check 3 FAIL: FAIL 已发生但 error-patterns.json 缺失'))
else:
    print('[quality-gate] ✅ Check 3: error-patterns 状态正确')

# --- Check 4: QGW-INDEX.md 存在 ---
if plan_count > 0 and not os.path.exists('docs/QGW-INDEX.md'):
    issues.append(('warn', f'Check 4 WARN: 有 plan/verification 但 QGW-INDEX.md 缺失'))
else:
    print('[quality-gate] ✅ Check 4: QGW-INDEX.md 存在')

# --- Check 5: 验收项有 source 引用 ---
items_without_source = []
for unit in data.get('units', []):
    for item in unit.get('items', []):
        source = item.get('source', '')
        if not source:
            items_without_source.append(item.get('id', 'unknown'))
if items_without_source:
    issues.append(('warn', f'Check 5 WARN: {len(items_without_source)} 项缺少 source 引用: {\"  \".join(items_without_source[:5])}'))
else:
    print('[quality-gate] ✅ Check 5: 所有 item 有 source 引用')

# --- Check 6: verifierReports 非空 ---
verifier_reports = data.get('verifierReports', [])
if not verifier_reports:
    issues.append(('block', f'Check 6 FAIL: verifierReports 为空 — 物证链缺失'))
else:
    print(f'[quality-gate] ✅ Check 6: verifierReports 非空 ({len(verifier_reports)} 条)')

# --- Check 7: 原有 PASS + toolCallId ---
fail_items = []
pending_items = []
skipped_items = []
missing_toolcall = []

for unit in data.get('units', []):
    unit_name = unit.get('name', 'unknown')
    for item in unit.get('items', []):
        item_id = item.get('id', 'unknown')
        status = item.get('status', 'PENDING')
        tool_call_id = item.get('toolCallId', '')

        if status == 'FAIL':
            fail_items.append(f'{item_id} ({unit_name})')
        elif status == 'PENDING':
            pending_items.append(f'{item_id} ({unit_name})')
        elif status == 'SKIPPED':
            skipped_items.append(f'{item_id} ({unit_name})')

        # SKIPPED 项不要求 toolCallId
        if status != 'SKIPPED' and not tool_call_id:
            missing_toolcall.append(f'{item_id} ({unit_name})')

if fail_items:
    issues.append(('block', f'Check 7a FAIL: {len(fail_items)} 项 FAIL — {\"  \".join(fail_items[:5])}'))
if pending_items:
    issues.append(('block', f'Check 7b FAIL: {len(pending_items)} 项 PENDING — {\"  \".join(pending_items[:5])}'))
if missing_toolcall:
    issues.append(('block', f'Check 7c FAIL: {len(missing_toolcall)} 项缺 toolCallId'))
if skipped_items:
    print(f'[quality-gate] ⚠️  Check 7d: {len(skipped_items)} 项 SKIPPED（增量模式，不阻止提交）')

if not fail_items and not pending_items and not missing_toolcall:
    pass_count = sum(1 for unit in data.get('units', []) for item in unit.get('items', []) if item.get('status') == 'PASS')
    skipped_count = len(skipped_items)
    if skipped_count > 0:
        print(f'[quality-gate] ✅ Check 7: PASS {pass_count} 项 + SKIPPED {skipped_count} 项（增量模式）')
    else:
        print(f'[quality-gate] ✅ Check 7: 全部 PASS ({pass_count} 项, 全部有 toolCallId)')

# --- Check 8: 引擎状态与验收数据一致性 ---
import os
engine_state_file = 'docs/.qgw-engine-state.json'
if os.path.exists(engine_state_file):
    try:
        with open(engine_state_file, 'r', encoding='utf-8') as f:
            engine = json.load(f)
        engine_gate = engine.get('gate', '')
        engine_steps = engine.get('steps', {})
        # 检查 S5/P5=COMPLETED 时验收 JSON 状态
        for check_step in ['S5', 'P5']:
            if check_step in engine_steps and engine_steps[check_step].get('status') == 'COMPLETED':
                # 检查是否有 PENDING items
                for unit in data.get('units', []):
                    for item in unit.get('items', []):
                        if item.get('status') == 'PENDING':
                            issues.append(('block', f'Check 8 FAIL: 引擎 {check_step}=COMPLETED 但 item {item.get("id")} 仍为 PENDING'))
                            break
        # 检查 S4/P4=COMPLETED 时 verifierReports 非空
        for check_step in ['S4', 'P4']:
            if check_step in engine_steps and engine_steps[check_step].get('status') == 'COMPLETED':
                if not data.get('verifierReports'):
                    issues.append(('block', f'Check 8 FAIL: 引擎 {check_step}=COMPLETED 但 verifierReports 为空'))
        # 检查 feedback_rounds 一致性
        engine_fb = engine.get('feedback_rounds', 0)
        json_fb = data.get('feedbackRounds', 0)
        if engine_fb != json_fb:
            issues.append(('warn', f'Check 8 WARN: 引擎 feedback_rounds={engine_fb} 与 JSON feedbackRounds={json_fb} 不一致'))
        print(f'[quality-gate] ✅ Check 8: 引擎状态与验收数据一致性检查完成')
    except (json.JSONDecodeError, IOError) as e:
        issues.append(('warn', f'Check 8 WARN: 引擎状态文件解析失败: {e}'))
else:
    print(f'[quality-gate] ℹ️  Check 8: 引擎未激活（无状态文件），跳过一致性检查')

# ===== 汇总 =====
block_issues = [i for i in issues if i[0] == 'block']
warn_issues = [i for i in issues if i[0] == 'warn']

for level, msg in issues:
    print(f'[quality-gate] {\"❌\" if level == \"block\" else \"⚠️ \"} {msg}')

if block_issues:
    print(f'')
    print(f'  文件: {latest_file}')
    print(f'  请修复所有问题后再提交。')
    print(f'  如需强制提交，请手动执行 git commit。')
    sys.exit(1)

# warn-only 模式
if warn_issues:
    print(f'')
    print(f'  ⚠️ {len(warn_issues)} 项警告（不阻止提交）')

print(f'[quality-gate] ✅ 所有检查通过')
sys.exit(0)
"
