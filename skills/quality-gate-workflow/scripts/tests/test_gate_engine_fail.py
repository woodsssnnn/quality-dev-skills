"""test_gate_engine_fail.py — GateEngine.fail() 正/负路径测试"""

import json
import os
from pathlib import Path

import pytest

from tests.conftest import COMPLETED, FAILED, NOT_STARTED, RUNNING


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _make_dirs(tmp_path):
    for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)


def _setup_gate1_p4(engine, tmp_path):
    """初始化 gate1 并快速推进到 P4 RUNNING 状态"""
    engine.init("gate1", "prd", [])
    _make_dirs(tmp_path)
    steps = engine.state["steps"]
    for s in ["P0", "P1", "P1.5", "P1.6", "P1.7", "P1-check", "P2", "P2.5", "P3"]:
        steps[s]["status"] = COMPLETED
    engine.enter("P4")


# ── fail 基本测试 ────────────────────────────────────────────────────────────

class TestFailBasic:

    def test_fail_step_success(self, engine_instance, tmp_path):
        """基本 fail：步骤 RUNNING → FAILED"""
        _setup_gate1_p4(engine_instance, tmp_path)
        rc = engine_instance.fail("P4", "验证不通过")
        # fail 返回 None（output_json 返回 None），不是 0/1
        assert engine_instance.state["steps"]["P4"]["status"] == FAILED

    def test_fail_rollback_code(self, engine_instance, tmp_path):
        """P4 CODE 根因回退到 P3"""
        _setup_gate1_p4(engine_instance, tmp_path)
        engine_instance.fail("P4", "代码问题", root_cause="CODE")
        assert engine_instance.state["steps"]["P3"]["status"] == NOT_STARTED

    def test_fail_rollback_plan(self, engine_instance, tmp_path):
        """P4 PLAN 根因回退到 P2"""
        _setup_gate1_p4(engine_instance, tmp_path)
        engine_instance.fail("P4", "Plan 不完整", root_cause="PLAN")
        assert engine_instance.state["steps"]["P2"]["status"] == NOT_STARTED

    def test_fail_not_running_blocked(self, engine_instance, tmp_path):
        """非 RUNNING 状态的步骤不能 fail"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)
        rc = engine_instance.fail("P0", "失败原因")
        assert rc == 1  # output_block 返回 1


class TestFailFeedback:

    def test_fail_feedback_rounds_increment(self, engine_instance, tmp_path):
        """P4 PLAN 根因使反馈轮次增加"""
        _setup_gate1_p4(engine_instance, tmp_path)
        engine_instance.fail("P4", "Plan 有问题", root_cause="PLAN")
        assert engine_instance.state["feedback_rounds"] == 1

    def test_fail_feedback_max_rounds_stop(self, engine_instance, tmp_path):
        """达到最大反馈轮次时返回 STOP"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)
        # 手动设置反馈轮次接近上限
        engine_instance.state["feedback_rounds"] = 1
        steps = engine_instance.state["steps"]
        for s in ["P0", "P1", "P1.5", "P1.6", "P1.7", "P1-check", "P2", "P2.5", "P3"]:
            steps[s]["status"] = COMPLETED
        engine_instance.enter("P4")
        rc = engine_instance.fail("P4", "Plan 仍有问题", root_cause="PLAN")
        # 达到上限应输出 STOP，rc 为 None（output_stop 返回 1）
        assert engine_instance.state["feedback_rounds"] == 2

    def test_fail_code_rounds_stop(self, engine_instance, tmp_path):
        """CODE 根因修复超过 2 轮应停止"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)
        engine_instance.state["code_feedback_rounds"] = 2
        steps = engine_instance.state["steps"]
        for s in ["P0", "P1", "P1.5", "P1.6", "P1.7", "P1-check", "P2", "P2.5", "P3"]:
            steps[s]["status"] = COMPLETED
        engine_instance.enter("P4")
        rc = engine_instance.fail("P4", "代码问题", root_cause="CODE")
        assert engine_instance.state["code_feedback_rounds"] == 3

    def test_fail_resets_rollback_target(self, engine_instance, tmp_path):
        """fail 后回退目标步骤重置为 NOT_STARTED，current_step 置空"""
        _setup_gate1_p4(engine_instance, tmp_path)
        engine_instance.fail("P4", "代码错误", root_cause="CODE")
        assert engine_instance.state["current_step"] is None
        assert engine_instance.state["steps"]["P3"]["status"] == NOT_STARTED
