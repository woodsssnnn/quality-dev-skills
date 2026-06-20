#!/usr/bin/env python3
"""progress-renderer.py — QGW 进度可视化渲染器

从引擎状态生成文本进度条，嵌入 status() 输出。

依赖: Python 3 stdlib only（无第三方依赖）
"""


# ===== 状态 emoji 映射 =====

_STATUS_EMOJI = {
    "COMPLETED": "✅",
    "FAILED": "❌",
    "RUNNING": "🔄",
    "SKIPPED": "⏭",
    "NOT_STARTED": "○",
}

_GATE_NAMES = {
    "gate1": "Gate 1",
    "gate2": "Gate 2",
    "debug": "Debug",
    "audit": "Audit",
}

# 进度条宽度
_BAR_WIDTH = 20
_FILL_CHAR = "█"
_EMPTY_CHAR = "░"


def render_progress(state: dict) -> str:
    """从引擎状态生成文本进度条。

    Args:
        state: gate-enforcer 的 state dict

    Returns:
        str: 多行文本进度条
    """
    gate = state.get("gate", "unknown")
    gate_name = _GATE_NAMES.get(gate, gate)
    session_id = state.get("session_id", "unknown")
    feedback = f"{state.get('feedback_rounds', 0)}/{state.get('max_feedback_rounds', 2)}"
    current = state.get("current_step")

    steps = state.get("steps", {})
    total = len(steps)
    completed = sum(1 for s in steps.values() if s["status"] == "COMPLETED")
    skipped = sum(1 for s in steps.values() if s["status"] == "SKIPPED")

    # 百分比
    progress_pct = round((completed + skipped) / total * 100, 0) if total > 0 else 0
    filled = int(_BAR_WIDTH * progress_pct / 100)
    bar = _FILL_CHAR * filled + _EMPTY_CHAR * (_BAR_WIDTH - filled)

    # 步骤流
    step_flow_parts = []
    for step_name, step_data in steps.items():
        emoji = _STATUS_EMOJI.get(step_data["status"], "?")
        step_flow_parts.append(f"{emoji}{step_name}")
    step_flow = " ".join(step_flow_parts)

    # 当前步骤说明
    current_info = f"当前: {current}" if current else "就绪"

    # 优先级信息
    priority_filter = state.get("priority_filter")
    priority_info = f" | 优先级: {', '.join(priority_filter)}" if priority_filter else ""

    lines = [
        f"{gate_name} [{bar}] {int(progress_pct)}% ({completed + skipped}/{total})",
        f"  {step_flow}",
        f"  {current_info} | 反馈: {feedback}{priority_info} | {session_id}",
    ]

    return "\n".join(lines)
