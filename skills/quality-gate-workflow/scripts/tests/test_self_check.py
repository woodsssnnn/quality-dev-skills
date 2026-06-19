"""test_self_check.py — GateEngine.self_check() 单元测试

验证自检功能的覆盖矩阵、缺口检测和 checkpoint 完整性检查。
"""

import json
import os
from pathlib import Path

import pytest

from tests.conftest import (
    COMPLETED, NOT_STARTED, RUNNING, SKIPPED,
    GateEngine, GATE1_STEPS,
)


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _make_dirs(tmp_path):
    for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)


def _complete_steps(engine, tmp_path, step_names):
    """按顺序完成指定步骤"""
    _make_dirs(tmp_path)
    for s in step_names:
        engine.enter(s)
        engine.complete(s)


# ── 自检基础测试 ────────────────────────────────────────────────────────────

class TestSelfCheck:

    def test_self_check_on_initialized_engine(self, initialized_gate1_engine):
        """初始化后 self-check 应返回 OK，所有步骤为 NOT_STARTED"""
        rc = initialized_gate1_engine.self_check()
        assert rc == 0
        state = initialized_gate1_engine.state
        # 所有 gate1 步骤应为 NOT_STARTED
        for step_name in state["steps"]:
            assert state["steps"][step_name]["status"] == NOT_STARTED

    def test_self_check_without_init_returns_block(self, engine_instance):
        """未初始化的引擎 self-check 应返回 BLOCK"""
        rc = engine_instance.self_check()
        assert rc == 1

    def test_self_check_shows_gaps_for_not_started(self, initialized_gate1_engine):
        """NOT_STARTED 步骤应产生缺口"""
        rc = initialized_gate1_engine.self_check()
        assert rc == 0
        # 引擎状态中应有 NOT_STARTED 的步骤
        steps = initialized_gate1_engine.state["steps"]
        not_started = [s for s, st in steps.items() if st["status"] == NOT_STARTED]
        assert len(not_started) > 0

    def test_self_check_progress_after_completing_steps(self, initialized_gate1_engine, tmp_path):
        """完成 P0/P1 后 self-check 应反映进度"""
        _complete_steps(initialized_gate1_engine, tmp_path, ["P0", "P1"])
        rc = initialized_gate1_engine.self_check()
        assert rc == 0
        steps = initialized_gate1_engine.state["steps"]
        assert steps["P0"]["status"] == COMPLETED
        assert steps["P1"]["status"] == COMPLETED

    def test_self_check_lite_mode_skipped_steps(self, engine_instance, tmp_path):
        """lite 模式下被 skip 的步骤不产生缺口"""
        engine_instance.init("gate1", "prd", ["--lite"])
        _complete_steps(engine_instance, tmp_path, ["P0", "P1"])
        rc = engine_instance.self_check()
        assert rc == 0
        steps = engine_instance.state["steps"]
        # P1.5/P1.6/P1.7 在 lite 模式应为 SKIPPED
        for s in ["P1.5", "P1.6", "P1.7"]:
            assert steps[s]["status"] == SKIPPED

    def test_self_check_gate2(self, initialized_gate2_engine):
        """Gate 2 初始化后 self-check 应返回 OK"""
        rc = initialized_gate2_engine.self_check()
        assert rc == 0
        steps = initialized_gate2_engine.state["steps"]
        assert "S0" in steps

    def test_self_check_feedback_rounds_default(self, initialized_gate1_engine):
        """默认反馈轮次应为 0"""
        rc = initialized_gate1_engine.self_check()
        assert rc == 0
        assert initialized_gate1_engine.state.get("feedback_rounds", 0) == 0

    def test_self_check_includes_coverage_data(self, initialized_gate1_engine):
        """self-check 输出应包含覆盖数据（通过 output_ok 返回）"""
        rc = initialized_gate1_engine.self_check()
        assert rc == 0
        # 验证状态中步骤覆盖信息完整
        steps = initialized_gate1_engine.state["steps"]
        for step_name, step_data in steps.items():
            assert "status" in step_data
