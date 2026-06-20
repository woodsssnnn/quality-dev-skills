#!/usr/bin/env python3
"""report-generator.py — QGW 报告自动生成器

根据引擎状态（state）和验证数据自动生成 6 种报告骨架。
确定性字段（日期/session_id/步骤流/统计）自动填充；
语义字段（偏差描述/根因分析）用 [PLACEHOLDER] 占位，供 LLM 补充。

用法:
    python report-generator.py generate --type <type> [--state <path>]

依赖: Python 3 stdlib only（无第三方依赖）
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path


# ===== 常量与映射 =====

REPORT_STEP_MAP = {
    "P3": "plan-completeness",
    "P4": "gate1-verifier",
    "S4": "audit",
    "D3": "debug-fix",
    "P5": "session-summary",
    "S5": "session-summary",
}

REPORT_DIR = "docs/reports"
SESSION_DIR = "docs/sessions"

STATUS_EMOJI = {
    "COMPLETED": "✅",
    "FAILED": "❌",
    "RUNNING": "🔄",
    "SKIPPED": "⏭ SKIP",
    "NOT_STARTED": "⏳",
}


# ===== 数据采集器 =====

def gather_verification_data(ver_dir: str) -> dict:
    """从 docs/verification/unit-*.json 采集验证统计数据。

    Returns:
        dict: 包含 units, total_items, pass_count, fail_count,
              pending_count, verifier_reports
    """
    result = {
        "units": [],
        "total_items": 0,
        "pass_count": 0,
        "fail_count": 0,
        "pending_count": 0,
        "verifier_reports": [],
    }

    ver_path = Path(ver_dir)
    if not ver_path.is_dir():
        return result

    for jf in sorted(ver_path.glob("unit-*.json")):
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        for unit in data.get("units", []):
            result["units"].append(unit)
            for item in unit.get("items", []):
                result["total_items"] += 1
                status = item.get("status", "")
                if status == "PASS":
                    result["pass_count"] += 1
                elif status == "FAIL":
                    result["fail_count"] += 1
                elif status == "PENDING":
                    result["pending_count"] += 1

        result["verifier_reports"].extend(data.get("verifierReports", []))

    return result


def gather_step_flow(state: dict) -> list:
    """从引擎状态构建步骤执行流列表。

    Returns:
        list[dict]: 每项含 step, status(emoji), notes
    """
    steps = state.get("steps", {})
    flow = []
    for step_name, step_data in steps.items():
        raw_status = step_data.get("status", "NOT_STARTED")
        emoji = STATUS_EMOJI.get(raw_status, "⏳")
        notes = ""
        if raw_status == "SKIPPED":
            notes = step_data.get("meta", {}).get("skip_reason", "")
        flow.append({
            "step": step_name,
            "status": emoji,
            "notes": notes,
        })
    return flow


# ===== 模板渲染器 =====

def _today() -> str:
    return datetime.date.today().isoformat()


def render_plan_completeness(state: dict, ver_data: dict) -> str:
    """渲染 Gate 1 Plan Completeness Report。"""
    session_id = state.get("session_id", "unknown")
    gate = state.get("gate", "gate1")
    mode = state.get("mode", "prd")

    total = ver_data.get("total_items", 0)
    covered = ver_data.get("pass_count", 0)
    missing = ver_data.get("fail_count", 0)
    partial = ver_data.get("pending_count", 0)

    # 渲染 units 行
    unit_rows = []
    for unit in ver_data.get("units", []):
        unit_id = unit.get("id", "?")
        for item in unit.get("items", []):
            item_id = item.get("id", "?")
            desc = item.get("description", "")
            item_status = item.get("status", "PENDING")
            judgment = {"PASS": "COVERED", "FAIL": "MISSING", "PENDING": "PARTIAL"}.get(item_status, "AMBIGUOUS")
            unit_rows.append(f"| {item_id} | {unit_id} | {desc[:40]} | {judgment} | — |")

    rows_str = "\n".join(unit_rows) if unit_rows else "| — | — | — | — | — |"

    return f"""## Plan Completeness Report

**日期**: {_today()}
**Session**: {session_id}
**Gate**: {gate} | **Mode**: {mode}

### 汇总

- COVERED: {covered} 项
- MISSING: {missing} 项
- PARTIAL: {partial} 项

**总体结论**: {"PASS" if missing == 0 else "FAIL"}

### 逐项详情

| Item ID | Unit | 描述 | 判定 | 说明 |
|---------|------|------|------|------|
{rows_str}

[PLACEHOLDER: 补充需求引用和计划章节映射]
"""


def render_gate1_verifier(state: dict, ver_data: dict) -> str:
    """渲染 Gate 1 Verifier Report。"""
    session_id = state.get("session_id", "unknown")
    total = ver_data.get("total_items", 0)
    covered = ver_data.get("pass_count", 0)
    partial = ver_data.get("fail_count", 0)
    missing = ver_data.get("pending_count", 0)

    overall = "COVERED" if missing == 0 and partial == 0 else ("PARTIAL" if partial > 0 else "MISSING")

    # 渲染 verifier reports
    vr_rows = []
    for vr in ver_data.get("verifier_reports", []):
        agent = vr.get("agent", "?")
        vr_result = vr.get("result", "?")
        ts = vr.get("timestamp", "?")
        vr_rows.append(f"| {agent} | {vr_result} | {ts} |")
    vr_str = "\n".join(vr_rows) if vr_rows else "| — | — | — |"

    return f"""## Gate 1 Verifier Report

**日期**: {_today()}
**Session**: {session_id}

### 汇总

- COVERED: {covered} 项
- PARTIAL: {partial} 项
- MISSING: {missing} 项

**总体结论**: {overall}

### Verifier 报告

| Agent | 结果 | 时间 |
|-------|------|------|
{vr_str}

[PLACEHOLDER: 逐章节详情和 PRD 资产检查]
"""


def render_gate2_audit(state: dict, ver_data: dict) -> str:
    """渲染 Gate 2 Audit Report。"""
    session_id = state.get("session_id", "unknown")
    gate = state.get("gate", "gate2")
    feedback = f"{state.get('feedback_rounds', 0)}/{state.get('max_feedback_rounds', 2)}"

    total = ver_data.get("total_items", 0)
    pass_count = ver_data.get("pass_count", 0)
    fail_count = ver_data.get("fail_count", 0)

    # Unit 汇总表
    unit_rows = []
    for unit in ver_data.get("units", []):
        unit_id = unit.get("id", "?")
        unit_name = unit.get("name", "?")
        unit_items = unit.get("items", [])
        unit_pass = sum(1 for it in unit_items if it.get("status") == "PASS")
        unit_fail = sum(1 for it in unit_items if it.get("status") == "FAIL")
        verdict = "PASS" if unit_fail == 0 else "FAIL"
        deviations = unit_fail
        unit_rows.append(f"| {unit_id}: {unit_name} | {verdict} | {deviations} | — |")
    unit_str = "\n".join(unit_rows) if unit_rows else "| — | — | — | — |"

    # 逐 item 详情
    item_rows = []
    for unit in ver_data.get("units", []):
        for item in unit.get("items", []):
            item_id = item.get("id", "?")
            desc = item.get("description", "")
            item_status = item.get("status", "?")
            tool_call_id = item.get("toolCallId", "—")
            code_refs = ", ".join(item.get("codeRefs", [])) or "—"
            item_rows.append(f"| {item_id} | {desc[:30]} | {item_status} | {code_refs} |")
    item_str = "\n".join(item_rows) if item_rows else "| — | — | — | — |"

    return f"""## Audit Report

**日期**: {_today()}
**Session**: {session_id}
**Gate**: {gate} | **反馈轮次**: {feedback}

### 汇总

| Unit | Verifier结论 | 偏差数 | 偏差详情 |
|------|-------------|--------|---------|
{unit_str}

**总计**: {pass_count} PASS / {fail_count} FAIL
**总体结论**: {"PASS" if fail_count == 0 else "FAIL"}

### 逐 Item 详情

| Item ID | 描述 | 判定 | 代码引用 |
|---------|------|------|---------|
{item_str}

### 收敛修复记录

[PLACEHOLDER: 修复轮次记录]

| Round | 修复项数 | 再验结果 | 剩余 |
|-------|---------|---------|------|
| — | — | — | — |
"""


def render_debug_fix(state: dict, ver_data: dict) -> str:
    """渲染 Debug Fix Verification Report。"""
    session_id = state.get("session_id", "unknown")
    mode = state.get("mode", "bug")

    # 从 D1 meta 提取修复标准（如果有）
    d1_meta = state.get("steps", {}).get("D1", {}).get("meta", {})
    fix_criteria = d1_meta.get("fix_criteria", "[PLACEHOLDER: 修复标准描述]")

    return f"""## Fix Verification

**日期**: {_today()}
**Session**: {session_id}
**Mode**: {mode}

### 修复标准

{fix_criteria}

### 验证结果

| 维度 | 判定 | 证据 |
|------|------|------|
| 症状消除 | [PLACEHOLDER] | [PLACEHOLDER] |
| 预期达成 | [PLACEHOLDER] | [PLACEHOLDER] |
| 回归完整 | [PLACEHOLDER] | [PLACEHOLDER] |
| 无 over-fixing | [PLACEHOLDER] | [PLACEHOLDER] |

**总体结论**: [PLACEHOLDER: PASS/FAIL]
"""


def render_session_summary(state: dict, ver_data: dict) -> str:
    """渲染 Session Summary。"""
    session_id = state.get("session_id", "unknown")
    gate = state.get("gate", "?")
    mode = state.get("mode", "?")
    flags = state.get("flags", [])
    trigger = " ".join([f"--{gate}"] + flags) if gate else "unknown"

    flow = gather_step_flow(state)
    flow_rows = []
    for f in flow:
        step = f["step"]
        status = f["status"]
        notes = f.get("notes", "")
        flow_rows.append(f"| {step} | {status} | {notes} |")
    flow_str = "\n".join(flow_rows) if flow_rows else "| — | — | — |"

    # 统计
    steps = state.get("steps", {})
    completed = sum(1 for s in steps.values() if s.get("status") == "COMPLETED")
    total = len(steps)
    skipped = sum(1 for s in steps.values() if s.get("status") == "SKIPPED")
    feedback = f"{state.get('feedback_rounds', 0)}/{state.get('max_feedback_rounds', 2)}"

    return f"""# QGW Session: {session_id}

**Date**: {_today()}
**Trigger**: {trigger}
**Gate**: {gate} | **Mode**: {mode}

## Execution Flow

| Step | Status | Notes |
|------|--------|-------|
{flow_str}

## 统计

- 完成: {completed}/{total}
- 跳过: {skipped}
- 反馈轮次: {feedback}

## Decisions

[PLACEHOLDER: 关键决策记录]

| Step | Decision | Rationale |
|------|----------|-----------|
| — | — | — |

## Bug Log

[PLACEHOLDER: Bug 日志]

| ID | Type | Source | Description | Root Cause | Fix |
|----|------|--------|-------------|------------|-----|
| — | — | — | — | — | — |

## Traceability

[PLACEHOLDER: 可追溯性矩阵]

| Item | Code Refs | Commit |
|------|-----------|--------|
| — | — | — |
"""


def render_prd_impact(state: dict, prd_data: dict) -> str:
    """渲染 PRD Revision Impact Report。"""
    session_id = state.get("session_id", "unknown")
    impact = prd_data.get("impact", "unknown")
    scope = prd_data.get("scope", "—")
    reset_steps = prd_data.get("reset_steps", [])
    reset_str = ", ".join(reset_steps) if reset_steps else "无"

    return f"""## PRD Revision Impact

**日期**: {_today()}
**Session**: {session_id}
**PRD Version**: [PLACEHOLDER: v(old) → v(new)]

### 修订摘要

[PLACEHOLDER: PRP 问题描述和建议修订的摘要]

### 影响分析

- **影响级别**: {impact}
- **变更范围**: {scope}
- **已重置步骤**: {reset_str}

### Plan 影响

| 章节 | Unit | 受影响项 | 当前状态 | 建议操作 |
|------|------|---------|---------|----------|
| [PLACEHOLDER] | — | — | — | — |

### Verification 影响

| 文件 | 受影响 item | 当前 status | 建议操作 |
|------|------------|-------------|----------|
| [PLACEHOLDER] | — | — | — |

### 建议

{"- [ ] 增量重跑 Gate 1（仅受影响章节）" if impact == "minor" else "- [ ] 全量重跑 Gate 1" if impact == "major" else "- [ ] 标记 Plan 受影响章节为 NEEDS_REVIEW"}
"""


# ===== 入口函数 =====

def generate_report(report_type: str, state: dict) -> str | None:
    """按类型生成报告，返回文件路径或 None。"""
    ver_dir = "docs/verification"
    ver_data = gather_verification_data(ver_dir)

    renderers = {
        "plan-completeness": ("reports", render_plan_completeness, ver_data),
        "gate1-verifier":    ("reports", render_gate1_verifier, ver_data),
        "audit":             ("reports", render_gate2_audit, ver_data),
        "debug-fix":         ("reports", render_debug_fix, ver_data),
        "session-summary":   ("sessions", render_session_summary, ver_data),
        "prd-impact":        ("reports", render_prd_impact, {}),
    }

    entry = renderers.get(report_type)
    if not entry:
        return None

    target_dir_name, renderer, context = entry

    # 确定输出目录
    if target_dir_name == "sessions":
        out_dir = Path(SESSION_DIR)
    else:
        out_dir = Path(REPORT_DIR)

    out_dir.mkdir(parents=True, exist_ok=True)

    # 渲染内容
    if report_type == "prd-impact":
        # prd-impact 需要 prd_data，从 state 中取
        prd_changes = state.get("prd_change", [])
        prd_data = prd_changes[-1] if prd_changes else {}
        content = renderer(state, prd_data)
    else:
        content = renderer(state, context)

    # 生成文件名
    date_str = _today()
    session_id = state.get("session_id", "unknown")
    safe_type = report_type.replace("-", "_")
    filename = f"{safe_type}-{date_str}-{session_id}.md"
    filepath = out_dir / filename

    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


def maybe_generate_report(step: str, state: dict) -> str | None:
    """引擎入口钩子：步骤完成时判断是否需要生成报告。

    被 gate-enforcer.py 的 complete() 方法调用。
    生成失败不阻断（warn-only），返回文件路径或 None。
    """
    report_type = REPORT_STEP_MAP.get(step)
    if not report_type:
        return None

    try:
        return generate_report(report_type, state)
    except Exception as e:
        print(f"[report-generator] ⚠️ 报告生成失败 ({report_type}): {e}", file=sys.stderr)
        return None


# ===== CLI =====

def main():
    parser = argparse.ArgumentParser(
        description="QGW 报告自动生成器 — 从引擎状态生成报告骨架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="action", help="可用操作")

    # generate
    p_gen = subparsers.add_parser("generate", help="生成指定类型的报告")
    p_gen.add_argument("--type", required=True,
                       choices=["plan-completeness", "gate1-verifier", "audit",
                                "debug-fix", "session-summary", "prd-impact"],
                       help="报告类型")
    p_gen.add_argument("--state", default="docs/.qgw-engine-state.json",
                       help="引擎状态文件路径")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    if args.action == "generate":
        state_path = Path(args.state)
        if not state_path.exists():
            print(f"ERROR: 状态文件不存在: {state_path}", file=sys.stderr)
            sys.exit(1)

        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)

        result = generate_report(args.type, state)
        if result:
            print(json.dumps({
                "status": "OK",
                "message": f"报告已生成: {result}",
                "path": result,
            }, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({
                "status": "ERROR",
                "message": f"无法生成报告类型: {args.type}",
            }, ensure_ascii=False, indent=2))
            sys.exit(1)


if __name__ == "__main__":
    main()
