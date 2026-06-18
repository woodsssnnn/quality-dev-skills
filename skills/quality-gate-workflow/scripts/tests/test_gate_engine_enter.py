"""test_gate_engine_enter.py — GateEngine.enter() 正/负路径测试"""

import json
import os
from pathlib import Path

import pytest

from tests.conftest import (
    COMPLETED, FAILED, GATE1_STEPS, GATE2_STEPS, NOT_STARTED, RUNNING, SKIPPED,
    GateEngine,
)


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _make_dirs(tmp_path):
    """创建产出物目录（P0 complete 需要 dirs_exist 检查）"""
    for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)


def _enter_and_complete_p0(engine, tmp_path):
    """进入并完成 P0 步骤（需要 dirs_exist 产出物检查）"""
    _make_dirs(tmp_path)
    engine.enter("P0")
    engine.complete("P0")


# ── Gate 1 enter 测试 ────────────────────────────────────────────────────────

class TestEnterGate1:

    def test_enter_p0_success(self, initialized_gate1_engine):
        """P0 无前置条件，可直接进入"""
        rc = initialized_gate1_engine.enter("P0")
        assert rc == 0
        assert initialized_gate1_engine.state["steps"]["P0"]["status"] == RUNNING

    def test_enter_p1_after_p0_complete(self, initialized_gate1_engine, tmp_path):
        """P0 完成后 P1 可进入"""
        _enter_and_complete_p0(initialized_gate1_engine, tmp_path)
        rc = initialized_gate1_engine.enter("P1")
        assert rc == 0
        assert initialized_gate1_engine.state["steps"]["P1"]["status"] == RUNNING

    def test_enter_blocked_prereq_not_met(self, initialized_gate1_engine):
        """P0 未完成时 P1 被阻止"""
        rc = initialized_gate1_engine.enter("P1")
        assert rc == 1

    def test_enter_completed_step_blocked(self, initialized_gate1_engine, tmp_path):
        """已完成的步骤不能再次进入"""
        _enter_and_complete_p0(initialized_gate1_engine, tmp_path)
        rc = initialized_gate1_engine.enter("P0")
        assert rc == 1

    def test_enter_skipped_step_returns_skip(self, engine_instance, tmp_path):
        """lite 模式下 P1.5 被 skip，enter 应返回 SKIP"""
        engine_instance.init("gate1", "prd", ["--lite"])
        # P0 → complete → P1 → complete → P1.5 应为 SKIPPED
        _make_dirs(tmp_path)
        engine_instance.enter("P0")
        engine_instance.complete("P0")
        engine_instance.enter("P1")
        engine_instance.complete("P1")
        rc = engine_instance.enter("P1.5")
        assert rc == 0  # output_skip 返回 0

    def test_enter_unknown_step_blocked(self, initialized_gate1_engine):
        rc = initialized_gate1_engine.enter("ZZZ")
        assert rc == 1

    def test_enter_running_mutex_blocked(self, initialized_gate1_engine, tmp_path):
        """有步骤正在 RUNNING 时，不能进入其他步骤"""
        _make_dirs(tmp_path)
        initialized_gate1_engine.enter("P0")
        # P0 正在 RUNNING，尝试 enter P1 应被阻止
        rc = initialized_gate1_engine.enter("P1")
        assert rc == 1

    def test_enter_p1_check_sub_decision_pass(self, initialized_gate1_engine, tmp_path):
        """P1.5/P1.6/P1.7 全部完成/跳过后 P1-check 可进入"""
        _make_dirs(tmp_path)
        # 用 lite 模式使 P1.5/P1.6/P1.7 被 skip
        engine = initialized_gate1_engine
        # 重新 init lite 模式
        engine.init("gate1", "prd", ["--lite"])
        engine.enter("P0")
        engine.complete("P0")
        engine.enter("P1")
        engine.complete("P1")
        # P1.5/P1.6/P1.7 已 SKIPPED → P1-check 可进入
        rc = engine.enter("P1-check")
        assert rc == 0

    def test_enter_p1_check_sub_decision_blocked(self, engine_instance, tmp_path):
        """P1.5 未完成时 P1-check 被阻止"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)
        engine_instance.enter("P0")
        engine_instance.complete("P0")
        engine_instance.enter("P1")
        engine_instance.complete("P1")
        # P1.5 仍为 NOT_STARTED → P1-check 被阻止
        rc = engine_instance.enter("P1-check")
        assert rc == 1

    def test_enter_sets_current_step(self, initialized_gate1_engine, tmp_path):
        _make_dirs(tmp_path)
        initialized_gate1_engine.enter("P0")
        assert initialized_gate1_engine.state["current_step"] == "P0"

    def test_enter_initializes_session_status(self, initialized_gate1_engine, tmp_path):
        """首次 enter 将会话状态从 INITIALIZED 改为 IN_PROGRESS"""
        _make_dirs(tmp_path)
        assert initialized_gate1_engine.state["status"] == "INITIALIZED"
        initialized_gate1_engine.enter("P0")
        assert initialized_gate1_engine.state["status"] == "IN_PROGRESS"


# ── Gate 2 / Debug / Audit enter 测试 ────────────────────────────────────────

class TestEnterOtherGates:

    def test_enter_s0_success_gate2(self, initialized_gate2_engine, tmp_path):
        """Gate 2 的 S0 无前置条件"""
        _make_dirs(tmp_path)
        rc = initialized_gate2_engine.enter("S0")
        assert rc == 0
        assert initialized_gate2_engine.state["steps"]["S0"]["status"] == RUNNING

    def test_enter_s2_after_s1_complete(self, initialized_gate2_engine, tmp_path):
        _make_dirs(tmp_path)
        initialized_gate2_engine.enter("S0")
        initialized_gate2_engine.complete("S0")
        initialized_gate2_engine.enter("S1")
        initialized_gate2_engine.complete("S1")
        rc = initialized_gate2_engine.enter("S2")
        assert rc == 0

    def test_enter_d1_success_debug(self, engine_instance, tmp_path):
        engine_instance.init("debug", "debug", [])
        rc = engine_instance.enter("D1")
        assert rc == 0

    def test_enter_a_success_audit(self, engine_instance, tmp_path):
        engine_instance.init("audit", "audit", [])
        rc = engine_instance.enter("A")
        assert rc == 0
