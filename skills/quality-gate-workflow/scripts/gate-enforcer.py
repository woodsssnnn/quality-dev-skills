#!/usr/bin/env python3
"""gate-enforcer.py — 确定性执行引擎 (Deterministic Execution Engine)

QGW 质量门禁工作流的步骤状态机。将"能 if-else 的规则"从 prompt 指令
提升为机械强制：步骤顺序、产出物存在性、格式校验、skip 条件合法性。

LLM 只做语义工作（理解需求、写 Plan、判断质量），引擎强制步骤纪律。

用法:
    python gate-enforcer.py init --gate gate1 [--mode prd|bug|opt] [--lite] [--strict] [--incremental] [--e2e]
    python gate-enforcer.py enter <step>
    python gate-enforcer.py complete <step> [--artifacts path1,path2] [--toolCallId id] [--meta json] [--skipReason text]
    python gate-enforcer.py fail <step> --reason <text> [--rootCause CODE|PLAN]
    python gate-enforcer.py status [--step <step>]
    python gate-enforcer.py resume

环境变量:
    QGW_ENGINE_ENABLED=true|false  — 启用/禁用引擎（默认 true）
    QGW_ENGINE_STATE=path          — 自定义状态文件路径（默认 docs/.qgw-engine-state.json）

依赖: Python 3 stdlib only（无第三方依赖）
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path

# ===== 常量 =====

SCHEMA_VERSION = "1.0"

# 状态文件默认路径
DEFAULT_STATE_FILE = "docs/.qgw-engine-state.json"
CHECKPOINT_DIR = "docs/.qgw-checkpoints"
GATE_STATE_FILE = "docs/.gate-state"

# 状态枚举
NOT_STARTED = "NOT_STARTED"
RUNNING = "RUNNING"
COMPLETED = "COMPLETED"
FAILED = "FAILED"
SKIPPED = "SKIPPED"

VALID_STEP_STATUSES = {NOT_STARTED, RUNNING, COMPLETED, FAILED, SKIPPED}
VALID_SESSION_STATUSES = {"INITIALIZED", "IN_PROGRESS", "PAUSED", "COMPLETED", "FAILED"}

# ===== 步骤定义 =====

GATE1_STEPS = ["P0", "P1", "P1.5", "P1.6", "P1.7", "P1-check", "P2", "P2.5", "P3", "P4", "P5"]
GATE2_STEPS = ["S0", "S1", "S2", "S2.5", "S3", "S3.5", "S4", "S4.5", "S5"]
DEBUG_STEPS = ["D1", "D2", "D3", "D4"]
AUDIT_STEPS = ["A", "B", "C", "D", "E"]

# ===== Guard 转换规则 =====
# requires: {前置步骤: 必须状态}
# skippable: 是否可以被标记为 SKIPPED
# artifact_checks: complete 时的产出物检查函数名
# pseudo: 虚拟步骤（不做语义工作，只做 guard 聚合）

TRANSITION_GUARDS = {
    # Gate 1
    "P0":       {"requires": {}, "artifact_checks": ["dirs_exist"]},
    "P1":       {"requires": {"P0": COMPLETED}},
    "P1.5":     {"requires": {"P1": COMPLETED}, "skippable": True},
    "P1.6":     {"requires": {"P1": COMPLETED}, "skippable": True},
    "P1.7":     {"requires": {"P1": COMPLETED}, "skippable": True},
    "P1-check": {"requires": {"P1": COMPLETED}, "pseudo": True,
                 "sub_decision_checks": ["P1.5", "P1.6", "P1.7"]},
    "P2":       {"requires": {"P1-check": COMPLETED}},
    "P2.5":     {"requires": {"P2": COMPLETED}, "skippable": True,
                 "artifact_checks": ["plan_files_exist"]},
    "P3":       {"requires": {"P2": COMPLETED}},
    "P4":       {"requires": {"P3": COMPLETED}},
    "P5":       {"requires": {"P4": COMPLETED},
                 "artifact_checks": ["verification_json_valid", "index_updated", "session_summary"]},

    # Gate 2
    "S0":       {"requires": {}, "artifact_checks": ["dirs_exist"]},
    "S1":       {"requires": {"S0": COMPLETED}},
    "S2":       {"requires": {"S1": COMPLETED}},
    "S2.5":     {"requires": {"S2": COMPLETED}},
    "S3":       {"requires": {"S2.5": COMPLETED}},
    "S3.5":     {"requires": {"S3": COMPLETED}, "skippable": True},
    "S4":       {"requires": {"S3": COMPLETED}},
    "S4.5":     {"requires": {"S4": COMPLETED}, "skippable": True},
    "S5":       {"requires": {"S4": COMPLETED},
                 "artifact_checks": ["toolcallid_complete", "coderefs_present", "plan_updated"]},

    # Debug
    "D1":       {"requires": {}},
    "D2":       {"requires": {"D1": COMPLETED}},
    "D3":       {"requires": {"D2": COMPLETED}},
    "D4":       {"requires": {"D3": COMPLETED}},

    # Audit
    "A":        {"requires": {}},
    "B":        {"requires": {"A": COMPLETED}},
    "C":        {"requires": {"B": COMPLETED}},
    "D":        {"requires": {"C": COMPLETED}},
    "E":        {"requires": {"D": COMPLETED}, "skippable": True},
}

# 需要 toolCallId 的步骤（verifier/顾问派发步骤）
TOOLCALL_REQUIRED_STEPS = {"P4", "S4", "P1.7", "P2.5", "D4", "C"}

# 反馈回路相关步骤
FEEDBACK_STEPS = {"P4", "S4"}

# 回退目标映射
ROLLBACK_TARGETS = {
    "P4": {"CODE": "P3", "PLAN": "P2"},
    "S4": {"CODE": "S2", "PLAN": "P2"},  # PLAN 根因反馈 Gate 1
}


# ===== 产出物检查器 =====

def check_dirs_exist(state):
    """检查 docs/ 子目录是否存在"""
    required_dirs = ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]
    missing = [d for d in required_dirs if not os.path.isdir(d)]
    if missing:
        return False, f"目录缺失: {', '.join(missing)}。请先创建"
    return True, "所有产出物目录存在"


def check_plan_files_exist(state):
    """检查 Plan 文件是否存在"""
    plans = list(Path("docs/plans").glob("*.md")) if os.path.isdir("docs/plans") else []
    if not plans:
        return False, "docs/plans/ 中无 Plan 文件"
    return True, f"Plan 文件存在 ({len(plans)} 个)"


def check_verification_json_valid(state):
    """检查验收 JSON 是否存在且格式有效"""
    ver_dir = Path("docs/verification")
    if not ver_dir.is_dir():
        return False, "docs/verification/ 不存在"
    json_files = list(ver_dir.glob("unit-*.json"))
    if not json_files:
        return False, "docs/verification/ 中无 unit-*.json 文件"
    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return False, f"{jf.name} 不是有效的 JSON 对象"
        except (json.JSONDecodeError, IOError) as e:
            return False, f"{jf.name} 解析失败: {e}"
    return True, f"验收 JSON 有效 ({len(json_files)} 个文件)"


def check_index_updated(state):
    """检查 QGW-INDEX.md 是否存在"""
    if not os.path.isfile("docs/QGW-INDEX.md"):
        return False, "docs/QGW-INDEX.md 不存在"
    return True, "QGW-INDEX.md 存在"


def check_session_summary(state):
    """检查 session summary 是否存在"""
    sessions_dir = Path("docs/sessions")
    if not sessions_dir.is_dir():
        return False, "docs/sessions/ 不存在"
    summaries = [f for f in sessions_dir.glob("*.md") if f.name != "INDEX.md"]
    if not summaries:
        return False, "docs/sessions/ 中无 session summary"
    return True, f"Session summary 存在 ({len(summaries)} 个)"


def check_toolcallid_complete(state):
    """检查所有 PASS 项是否有 toolCallId"""
    ver_dir = Path("docs/verification")
    if not ver_dir.is_dir():
        return False, "docs/verification/ 不存在"
    for jf in ver_dir.glob("unit-*.json"):
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
            for unit in data.get("units", []):
                for item in unit.get("items", []):
                    if item.get("status") == "PASS" and not item.get("toolCallId"):
                        return False, f"{jf.name}: item {item.get('id')} 为 PASS 但缺 toolCallId"
        except (json.JSONDecodeError, IOError):
            pass
    return True, "所有 PASS 项有 toolCallId"


def check_coderefs_present(state):
    """检查 PASS 项是否有 codeRefs"""
    ver_dir = Path("docs/verification")
    if not ver_dir.is_dir():
        return True, "无 verification 目录（跳过 codeRefs 检查）"
    for jf in ver_dir.glob("unit-*.json"):
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
            for unit in data.get("units", []):
                for item in unit.get("items", []):
                    if item.get("status") == "PASS" and not item.get("codeRefs"):
                        return False, f"{jf.name}: item {item.get('id')} 为 PASS 但缺 codeRefs"
        except (json.JSONDecodeError, IOError):
            pass
    return True, "所有 PASS 项有 codeRefs"


def check_plan_updated(state):
    """检查 Plan 文件是否已更新（Gate 2 完成后应有实现记录）"""
    plans = list(Path("docs/plans").glob("*.md")) if os.path.isdir("docs/plans") else []
    if not plans:
        return False, "docs/plans/ 中无 Plan 文件"
    return True, "Plan 文件存在"


ARTIFACT_CHECKERS = {
    "dirs_exist": check_dirs_exist,
    "plan_files_exist": check_plan_files_exist,
    "verification_json_valid": check_verification_json_valid,
    "index_updated": check_index_updated,
    "session_summary": check_session_summary,
    "toolcallid_complete": check_toolcallid_complete,
    "coderefs_present": check_coderefs_present,
    "plan_updated": check_plan_updated,
}


# ===== 工具函数 =====

def now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")


def generate_session_id():
    ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    rand = hashlib.md5(ts.encode()).hexdigest()[:6]
    return f"ses_{ts}_{rand}"


def validate_toolcallid(tcid, step):
    """验证 toolCallId 格式: Agent|<step>|<ISO-timestamp>"""
    if not tcid:
        return False, "toolCallId 为空"
    parts = tcid.split("|")
    if len(parts) < 3:
        return False, f"格式无效（期望至少 3 段 '|'-分隔）: {tcid}"
    if parts[0] != "Agent":
        return False, f"前缀必须为 'Agent'（禁止 'main|'）: {tcid}"
    if parts[1] != step:
        return False, f"步骤标识不匹配（期望 '{step}'，实际 '{parts[1]}'）: {tcid}"
    # 尝试解析时间戳
    ts_str = "|".join(parts[2:])  # 时间戳可能含 '|'
    try:
        datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except ValueError:
        return False, f"时间戳格式无效: {ts_str}"
    return True, "格式有效"


def output_json(data):
    """输出 JSON 结果到 stdout"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def output_ok(message, **extra):
    result = {"status": "OK", "message": message, "timestamp": now_iso()}
    result.update(extra)
    output_json(result)
    return 0


def output_allow(step, message, **extra):
    result = {"status": "ALLOW", "step": step, "message": message, "timestamp": now_iso()}
    result.update(extra)
    output_json(result)
    return 0


def output_block(reason, **extra):
    result = {
        "status": "BLOCK",
        "reason": reason,
        "hint": "请修复上述问题后重试。参考: anti-patterns.md",
        "timestamp": now_iso(),
    }
    result.update(extra)
    output_json(result)
    return 1


def output_skip(step, reason):
    result = {"status": "SKIP", "step": step, "reason": reason, "timestamp": now_iso()}
    output_json(result)
    return 0


def output_stop(message, **extra):
    result = {"status": "STOP", "message": message, "timestamp": now_iso()}
    result.update(extra)
    output_json(result)
    return 1


# ===== 引擎核心 =====

class GateEngine:
    def __init__(self, state_file=None):
        self.state_file = state_file or os.environ.get("QGW_ENGINE_STATE", DEFAULT_STATE_FILE)
        self.state = self._load_state()

    # ===== 状态持久化 =====

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[gate-enforcer] ⚠️ 状态文件损坏: {e}", file=sys.stderr)
                return None
        return None

    def _save_state(self):
        os.makedirs(os.path.dirname(self.state_file) or ".", exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def _ensure_state(self):
        if not self.state:
            return False
        return True

    # ===== Checkpoint =====

    def _write_checkpoint(self, step, step_state):
        os.makedirs(CHECKPOINT_DIR, exist_ok=True)
        artifacts = step_state.get("artifacts", [])
        # 计算产出物 checksum
        checksum_parts = []
        for a in sorted(artifacts):
            if os.path.isfile(a):
                with open(a, "rb") as f:
                    checksum_parts.append(hashlib.sha256(f.read()).hexdigest())
        checksum = hashlib.sha256("|".join(checksum_parts).encode()).hexdigest()[:16] if checksum_parts else "no-artifacts"

        cp = {
            "schema_version": SCHEMA_VERSION,
            "session_id": self.state["session_id"],
            "step": step,
            "status": step_state["status"],
            "timestamp": step_state.get("completed_at", now_iso()),
            "prerequisites_met": self._check_prereqs_snapshot(step),
            "artifacts": artifacts,
            "toolCallId": step_state.get("meta", {}).get("toolCallId"),
            "checksum": f"sha256:{checksum}",
        }
        # 规范化 step 名用于文件名
        safe_name = step.replace(".", "_")
        cp_path = os.path.join(CHECKPOINT_DIR, f"{safe_name}.json")
        with open(cp_path, "w", encoding="utf-8") as f:
            json.dump(cp, f, indent=2, ensure_ascii=False)

    def _check_prereqs_snapshot(self, step):
        """记录当前步骤的前置条件状态快照"""
        guard = TRANSITION_GUARDS.get(step, {})
        snapshot = {}
        for prereq in guard.get("requires", {}):
            prereq_state = self.state.get("steps", {}).get(prereq, {})
            snapshot[prereq] = prereq_state.get("status", NOT_STARTED)
        return snapshot

    # ===== .gate-state 兼容写入 =====

    def _update_gate_state(self):
        """写入兼容 verify-checkpoint.sh 的 .gate-state 文件"""
        if not self.state:
            return
        gate = self.state.get("gate", "")
        steps = self.state.get("steps", {})

        # 判断 Gate 1 是否全部完成
        gate1_key_steps = ["P0", "P1", "P1-check", "P2", "P3", "P4", "P5"]
        gate1_done = all(
            steps.get(s, {}).get("status") in (COMPLETED, SKIPPED)
            for s in gate1_key_steps
            if s in steps
        )

        # 判断 Gate 2 是否全部完成
        gate2_key_steps = ["S0", "S1", "S2", "S2.5", "S3", "S4", "S5"]
        gate2_done = all(
            steps.get(s, {}).get("status") in (COMPLETED, SKIPPED)
            for s in gate2_key_steps
            if s in steps
        )

        os.makedirs("docs", exist_ok=True)
        with open(GATE_STATE_FILE, "w", encoding="utf-8") as f:
            if gate2_done and gate == "gate2":
                f.write("verified")
            elif gate1_done and gate == "gate1":
                f.write("plan")
            elif gate == "gate2":
                f.write("code")
            else:
                f.write("plan")

    # ===== Skip 矩阵 =====

    def _build_skip_matrix(self, gate, mode, flags):
        """在 init 时确定哪些步骤可跳过"""
        skips = {}
        flag_set = set(flags) if flags else set()

        if gate == "gate1":
            if "--lite" in flag_set:
                skips["P1.5"] = "lite-mode"
                skips["P1.6"] = "lite-mode"
                skips["P1.7"] = "lite-mode"

        if gate == "gate2":
            if "--e2e" not in flag_set:
                skips["S4.5"] = "no-e2e-flag"

        return skips

    def _apply_content_driven_skips(self, meta):
        """基于内容驱动的 skip（如 P1 complete 时声明 has_backend=false → SKIP P1.5）"""
        if not meta:
            return []
        applied = []
        current_step = self.state.get("current_step")

        # P1 complete 时：纯前端无 DB 变更 → SKIP P1.5
        if current_step == "P1" and meta.get("has_backend") is False:
            if "P1.5" in self.state.get("steps", {}):
                p15 = self.state["steps"]["P1.5"]
                if p15["status"] == NOT_STARTED:
                    p15["status"] = SKIPPED
                    p15["meta"] = {"skip_reason": "纯前端需求，无 SQL/Mapper/Service/Liquibase 变更"}
                    applied.append(("P1.5", "纯前端需求，无 DB 变更"))

        # P1 complete 时：全新独立项目 → SKIP P1.6
        if current_step == "P1" and meta.get("is_greenfield") is True:
            if "P1.6" in self.state.get("steps", {}):
                p16 = self.state["steps"]["P1.6"]
                if p16["status"] == NOT_STARTED:
                    p16["status"] = SKIPPED
                    p16["meta"] = {"skip_reason": "全新独立项目，无已有代码"}
                    applied.append(("P1.6", "全新独立项目"))

        return applied

    # ===== 步骤列表 =====

    def _get_steps(self, gate):
        if gate == "gate1":
            return GATE1_STEPS
        elif gate == "gate2":
            return GATE2_STEPS
        elif gate == "debug":
            return DEBUG_STEPS
        elif gate == "audit":
            return AUDIT_STEPS
        return []

    def _next_step(self, current):
        """计算下一个待执行步骤"""
        steps = list(self.state["steps"].keys())
        if current not in steps:
            return None
        idx = steps.index(current)
        for i in range(idx + 1, len(steps)):
            next_s = steps[i]
            if self.state["steps"][next_s]["status"] not in (SKIPPED,):
                return next_s
        return "SESSION_COMPLETE"

    # ===== INIT =====

    def init(self, gate, mode, flags):
        """初始化新的执行会话"""
        if self.state and self.state.get("status") == "IN_PROGRESS":
            return output_block(
                f"已有进行中的会话 ({self.state.get('session_id')})。"
                f"请先 complete 或使用 resume 恢复",
                current_session=self.state.get("session_id")
            )

        steps = self._get_steps(gate)
        if not steps:
            return output_block(f"无效的 gate: {gate}（有效值: gate1, gate2, debug, audit）")

        session_id = generate_session_id()
        skip_matrix = self._build_skip_matrix(gate, mode, flags)

        self.state = {
            "schema_version": SCHEMA_VERSION,
            "session_id": session_id,
            "gate": gate,
            "mode": mode or "default",
            "flags": flags or [],
            "status": "INITIALIZED",
            "current_step": None,
            "steps": {},
            "skip_matrix": skip_matrix,
            "feedback_rounds": 0,
            "max_feedback_rounds": 2,
            "created_at": now_iso(),
        }

        # 初始化所有步骤状态
        for s in steps:
            status = SKIPPED if s in skip_matrix else NOT_STARTED
            self.state["steps"][s] = {
                "status": status,
                "started_at": None,
                "completed_at": None,
                "artifacts": [],
                "meta": {},
            }
            if s in skip_matrix:
                self.state["steps"][s]["meta"]["skip_reason"] = skip_matrix[s]

        self._save_state()
        self._update_gate_state()

        skipped_info = skip_matrix if skip_matrix else "无"
        return output_ok(
            f"会话初始化完成",
            session_id=session_id,
            gate=gate,
            mode=mode,
            steps=steps,
            skipped=skipped_info,
        )

    # ===== ENTER =====

    def enter(self, step):
        """LLM 请求进入某步骤——前置 guard 检查"""
        if not self._ensure_state():
            return output_block("引擎未初始化。请先运行 init")

        steps = self.state.get("steps", {})
        if step not in steps:
            return output_block(f"未知步骤: {step}（当前 gate={self.state.get('gate')}）")

        step_state = steps[step]

        # 检查1: 步骤是否已完成或已跳过
        if step_state["status"] == COMPLETED:
            return output_block(f"步骤 {step} 已完成，无需重复执行")
        if step_state["status"] == SKIPPED:
            reason = step_state.get("meta", {}).get("skip_reason", "已标记为跳过")
            return output_skip(step, reason)

        # 检查2: 前置步骤是否满足
        guard = TRANSITION_GUARDS.get(step, {})
        for prereq, required_status in guard.get("requires", {}).items():
            prereq_state = steps.get(prereq)
            if not prereq_state:
                return output_block(f"前置步骤 {prereq} 不存在（内部错误）", step=step)
            prereq_status = prereq_state["status"]
            if prereq_status != required_status:
                # SKIPPED 也算满足（对 skippable 步骤）
                if prereq_status == SKIPPED and TRANSITION_GUARDS.get(prereq, {}).get("skippable"):
                    continue
                return output_block(
                    f"前置条件不满足: {prereq}={prereq_status} (需要 {required_status})",
                    step=step,
                    anti_pattern=self._suggest_anti_pattern(step, prereq)
                )

        # 检查3: P1-check 虚拟步骤的额外检查——P1.5/P1.6/P1.7 必须已决策
        if step == "P1-check":
            sub_checks = guard.get("sub_decision_checks", [])
            for sub in sub_checks:
                sub_state = steps.get(sub, {})
                sub_status = sub_state.get("status")
                if sub_status not in (COMPLETED, SKIPPED):
                    return output_block(
                        f"P1-check 前置: {sub} 状态为 {sub_status}，必须为 COMPLETED 或 SKIPPED",
                        step=step,
                        anti_pattern="#23"
                    )

        # 检查4: 是否有其他步骤正在 RUNNING
        for s, st in steps.items():
            if st["status"] == RUNNING and s != step:
                return output_block(
                    f"步骤 {s} 正在执行中，请先 complete {s} 再进入 {step}",
                    step=step
                )

        # 全部通过 → 允许进入
        step_state["status"] = RUNNING
        step_state["started_at"] = now_iso()
        self.state["current_step"] = step
        if self.state["status"] == "INITIALIZED":
            self.state["status"] = "IN_PROGRESS"
        self._save_state()

        return output_allow(step, f"进入 {step}，前置条件已满足")

    # ===== COMPLETE =====

    def complete(self, step, artifacts=None, tool_call_id=None, meta=None, skip_reason=None):
        """LLM 声明步骤完成——做产出物验证"""
        if not self._ensure_state():
            return output_block("引擎未初始化")

        steps = self.state.get("steps", {})
        if step not in steps:
            return output_block(f"未知步骤: {step}")

        step_state = steps[step]
        if step_state["status"] != RUNNING:
            return output_block(f"步骤 {step} 状态为 {step_state['status']}，非 RUNNING。请先 enter {step}")

        # 产出物存在性检查
        artifact_list = []
        if artifacts:
            for ap in artifacts:
                ap = ap.strip()
                if not ap:
                    continue
                if not os.path.exists(ap):
                    return output_block(
                        f"产出物不存在: {ap}。请先用 Write 工具创建文件，再调用 complete",
                        step=step
                    )
                artifact_list.append(ap)

        # toolCallId 强制检查（verifier/顾问步骤）
        if step in TOOLCALL_REQUIRED_STEPS:
            if not tool_call_id:
                return output_block(
                    f"步骤 {step} 需要 toolCallId。请通过 Task/Agent 工具派发子代理后提供",
                    step=step,
                    anti_pattern="#1" if step in ("P4", "S4") else "#27"
                )
            valid, msg = validate_toolcallid(tool_call_id, step)
            if not valid:
                return output_block(
                    f"toolCallId 格式无效: {msg}。期望格式: Agent|{step}|ISO-timestamp",
                    step=step,
                    anti_pattern="#21"
                )

        # Guard 定义的产出物检查
        guard = TRANSITION_GUARDS.get(step, {})
        for check_name in guard.get("artifact_checks", []):
            checker = ARTIFACT_CHECKERS.get(check_name)
            if checker:
                ok, msg = checker(self.state)
                if not ok:
                    return output_block(
                        f"产出物检查失败 [{check_name}]: {msg}",
                        step=step
                    )

        # 标记完成
        step_state["status"] = COMPLETED
        step_state["completed_at"] = now_iso()
        step_state["artifacts"] = artifact_list
        if tool_call_id:
            step_state["meta"]["toolCallId"] = tool_call_id
        if meta:
            step_state["meta"].update(meta)

        # 写 checkpoint
        self._write_checkpoint(step, step_state)

        # 内容驱动的 skip（如 P1 complete 后根据 meta 跳过 P1.5）
        applied_skips = self._apply_content_driven_skips(meta)

        # 更新 .gate-state
        self._update_gate_state()

        # 计算下一步
        self.state["current_step"] = None
        next_step = self._next_step(step)

        # 如果所有步骤完成，更新会话状态
        if next_step == "SESSION_COMPLETE":
            self.state["status"] = "COMPLETED"

        self._save_state()

        result_extras = {
            "step": step,
            "completed_at": step_state["completed_at"],
            "next_step": next_step,
        }
        if applied_skips:
            result_extras["applied_skips"] = [
                {"step": s, "reason": r} for s, r in applied_skips
            ]

        return output_ok(f"{step} 完成。下一步: {next_step}", **result_extras)

    # ===== FAIL =====

    def fail(self, step, reason, root_cause=None):
        """标记步骤失败，确定回退目标"""
        if not self._ensure_state():
            return output_block("引擎未初始化")

        steps = self.state.get("steps", {})
        if step not in steps:
            return output_block(f"未知步骤: {step}")

        step_state = steps[step]
        if step_state["status"] != RUNNING:
            return output_block(f"步骤 {step} 状态为 {step_state['status']}，非 RUNNING")

        step_state["status"] = FAILED
        step_state["meta"]["fail_reason"] = reason
        if root_cause:
            step_state["meta"]["rootCause"] = root_cause

        # 确定回退目标
        rollback_target = None
        if step in ROLLBACK_TARGETS:
            rc = root_cause or "CODE"
            rollback_target = ROLLBACK_TARGETS[step].get(rc)

        # 反馈回路计数
        if step in FEEDBACK_STEPS and root_cause == "PLAN":
            self.state["feedback_rounds"] += 1
            if self.state["feedback_rounds"] >= self.state["max_feedback_rounds"]:
                self._save_state()
                return output_stop(
                    f"已达最大反馈轮次 ({self.state['max_feedback_rounds']})，停止并交由用户决策",
                    step=step,
                    feedback_rounds=f"{self.state['feedback_rounds']}/{self.state['max_feedback_rounds']}"
                )

        # 回退目标步骤重置为 NOT_STARTED
        if rollback_target and rollback_target in steps:
            steps[rollback_target]["status"] = NOT_STARTED

        self.state["current_step"] = None
        self._save_state()

        feedback_info = ""
        if step in FEEDBACK_STEPS:
            feedback_info = f" | 反馈轮次: {self.state['feedback_rounds']}/{self.state['max_feedback_rounds']}"

        return output_json({
            "status": "FAIL",
            "step": step,
            "reason": reason,
            "root_cause": root_cause or "CODE",
            "rollback_to": rollback_target,
            "feedback_rounds": f"{self.state['feedback_rounds']}/{self.state['max_feedback_rounds']}",
            "message": f"{step} 失败。回退到: {rollback_target or '无'}{feedback_info}",
            "timestamp": now_iso(),
        }) or 1

    # ===== STATUS =====

    def status(self, step=None):
        """查询状态——被 --self 和 health-check.sh 读取"""
        if not self._ensure_state():
            return output_block("引擎未初始化")

        if step:
            step_state = self.state.get("steps", {}).get(step)
            if not step_state:
                return output_block(f"未知步骤: {step}")
            return output_ok(f"步骤 {step} 状态", step=step, **step_state)

        steps = self.state.get("steps", {})
        total = len(steps)
        completed = sum(1 for s in steps.values() if s["status"] == COMPLETED)
        skipped = sum(1 for s in steps.values() if s["status"] == SKIPPED)
        failed = sum(1 for s in steps.values() if s["status"] == FAILED)
        running = sum(1 for s in steps.values() if s["status"] == RUNNING)

        progress_pct = round((completed + skipped) / total * 100, 1) if total > 0 else 0

        return output_ok(
            f"会话 {self.state.get('session_id')} | "
            f"进度: {completed}/{total} ({progress_pct}%)",
            session_id=self.state["session_id"],
            gate=self.state["gate"],
            mode=self.state.get("mode"),
            session_status=self.state["status"],
            current_step=self.state.get("current_step"),
            progress={
                "completed": completed,
                "skipped": skipped,
                "failed": failed,
                "running": running,
                "total": total,
                "percentage": progress_pct,
            },
            steps={s: st["status"] for s, st in steps.items()},
            skip_matrix=self.state.get("skip_matrix", {}),
            feedback_rounds=f"{self.state['feedback_rounds']}/{self.state['max_feedback_rounds']}",
        )

    # ===== RESUME =====

    def resume(self):
        """从文件恢复状态（compaction recovery）"""
        if not self._ensure_state():
            return output_block("引擎未初始化，无法恢复")

        # 重新验证文件存在性
        steps = self.state.get("steps", {})
        inconsistencies = []
        for s, st in steps.items():
            if st["status"] == COMPLETED:
                # 检查 checkpoint 文件是否存在
                safe_name = s.replace(".", "_")
                cp_path = os.path.join(CHECKPOINT_DIR, f"{safe_name}.json")
                if not os.path.exists(cp_path):
                    inconsistencies.append(f"{s}: 状态=COMPLETED 但 checkpoint 文件缺失")

        if inconsistencies:
            return output_block(
                f"状态不一致:\n" + "\n".join(f"  - {i}" for i in inconsistencies) +
                "\n请检查后重试",
                inconsistencies=inconsistencies
            )

        self._update_gate_state()
        return output_ok(
            f"会话恢复成功",
            session_id=self.state["session_id"],
            current_step=self.state.get("current_step"),
            gate=self.state["gate"],
        )

    # ===== 辅助方法 =====

    def _suggest_anti_pattern(self, step, prereq):
        """根据步骤和前置条件建议相关的反模式编号"""
        mapping = {
            ("P2", "P1-check"): "#23",
            ("P5", "P4"): "#1",
            ("S5", "S4"): "#1",
        }
        return mapping.get((step, prereq), "")


# ===== CLI 入口 =====

def main():
    parser = argparse.ArgumentParser(
        description="QGW 确定性执行引擎 — 步骤状态机 + Guard 检查",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="action", help="可用操作")

    # init
    p_init = subparsers.add_parser("init", help="初始化新的执行会话")
    p_init.add_argument("--gate", required=True, choices=["gate1", "gate2", "debug", "audit"],
                        help="门禁类型")
    p_init.add_argument("--mode", default=None,
                        choices=["prd", "bug", "opt", "impl", "debug", "audit"],
                        help="工作模式")
    p_init.add_argument("--lite", action="store_true", help="轻量快速通道")
    p_init.add_argument("--strict", action="store_true", help="零偏差模式")
    p_init.add_argument("--incremental", action="store_true", help="增量验证")
    p_init.add_argument("--e2e", action="store_true", help="E2E 行为验证")

    # enter
    p_enter = subparsers.add_parser("enter", help="请求进入某步骤（前置检查）")
    p_enter.add_argument("step", help="步骤标识（如 P0, P1, S2.5）")

    # complete
    p_complete = subparsers.add_parser("complete", help="声明步骤完成")
    p_complete.add_argument("step", help="步骤标识")
    p_complete.add_argument("--artifacts", default=None,
                            help="产出物路径（逗号分隔）")
    p_complete.add_argument("--toolCallId", default=None,
                            help="Task/Agent 工具调用 ID（verifier/顾问步骤必选）")
    p_complete.add_argument("--meta", default=None,
                            help="附加元数据（JSON 字符串）")
    p_complete.add_argument("--skipReason", default=None,
                            help="跳过原因（用于 SKIPPED 步骤）")

    # fail
    p_fail = subparsers.add_parser("fail", help="标记步骤失败")
    p_fail.add_argument("step", help="步骤标识")
    p_fail.add_argument("--reason", required=True, help="失败原因")
    p_fail.add_argument("--rootCause", default=None, choices=["CODE", "PLAN"],
                        help="根因分类")

    # status
    p_status = subparsers.add_parser("status", help="查询当前状态")
    p_status.add_argument("--step", default=None, help="查询特定步骤")

    # resume
    subparsers.add_parser("resume", help="从文件恢复状态（compaction recovery）")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    engine = GateEngine()

    if args.action == "init":
        flags = []
        if args.lite:
            flags.append("--lite")
        if args.strict:
            flags.append("--strict")
        if args.incremental:
            flags.append("--incremental")
        if args.e2e:
            flags.append("--e2e")
        rc = engine.init(args.gate, args.mode, flags)

    elif args.action == "enter":
        rc = engine.enter(args.step)

    elif args.action == "complete":
        artifacts = None
        if args.artifacts:
            artifacts = [a.strip() for a in args.artifacts.split(",") if a.strip()]
        meta = None
        if args.meta:
            try:
                meta = json.loads(args.meta)
            except json.JSONDecodeError as e:
                rc = output_block(f"--meta JSON 解析失败: {e}")
                sys.exit(rc)
        rc = engine.complete(args.step, artifacts=artifacts,
                             tool_call_id=args.toolCallId, meta=meta,
                             skip_reason=args.skipReason)

    elif args.action == "fail":
        rc = engine.fail(args.step, args.reason, root_cause=args.rootCause)

    elif args.action == "status":
        rc = engine.status(step=args.step)

    elif args.action == "resume":
        rc = engine.resume()

    else:
        parser.print_help()
        rc = 1

    sys.exit(rc or 0)


if __name__ == "__main__":
    main()
