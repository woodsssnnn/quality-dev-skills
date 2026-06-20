"""test_auto_complete.py — 自动完成机制测试

P0/S0/P1-check 等纯机械步骤在 enter 时自动 complete。
"""

import json
import os
from pathlib import Path

import pytest

from tests.conftest import COMPLETED, NOT_STARTED, RUNNING, SKIPPED, GateEngine, AUTO_COMPLETE_STEPS


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _make_dirs(tmp_path):
    for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)


# ===== TestAutoComplete =====

class TestAutoComplete:

    def test_auto_complete_steps_defined(self):
        """AUTO_COMPLETE_STEPS 常量包含 P0/S0/P1-check。"""
        assert "P0" in AUTO_COMPLETE_STEPS
        assert "S0" in AUTO_COMPLETE_STEPS
        assert "P1-check" in AUTO_COMPLETE_STEPS

    def test_p0_auto_completes(self, engine_instance, tmp_path):
        """enter P0 时如果 artifact check 通过应自动 complete。"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)

        rc = engine_instance.enter("P0")
        assert rc == 0
        # P0 应直接 COMPLETED（不是 RUNNING）
        assert engine_instance.state["steps"]["P0"]["status"] == COMPLETED

    def test_s0_auto_completes(self, engine_instance, tmp_path):
        """enter S0 时应自动 complete。"""
        engine_instance.init("gate2", "prd", [])
        _make_dirs(tmp_path)

        rc = engine_instance.enter("S0")
        assert rc == 0
        assert engine_instance.state["steps"]["S0"]["status"] == COMPLETED

    def test_non_auto_step_stays_running(self, engine_instance, tmp_path):
        """非 auto-complete 步骤 enter 后应保持 RUNNING。"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)
        # P0 auto-complete 后才能 enter P1
        engine_instance.enter("P0")

        rc = engine_instance.enter("P1")
        assert rc == 0
        assert engine_instance.state["steps"]["P1"]["status"] == RUNNING

    def test_auto_complete_outputs_marker(self, engine_instance, tmp_path):
        """auto-complete 的输出应包含 auto_completed 标记。"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)

        rc = engine_instance.enter("P0")
        assert rc == 0
        # meta 中应有 auto_completed 标记
        meta = engine_instance.state["steps"]["P0"]["meta"]
        assert meta.get("auto_completed") is True

    def test_auto_complete_fails_gracefully(self, engine_instance, tmp_path):
        """auto-complete 步骤如果 artifact check 失败应正常 BLOCK。"""
        engine_instance.init("gate1", "prd", [])
        # 不创建 docs/ 目录，dirs_exist 检查应失败
        rc = engine_instance.enter("P0")
        assert rc == 1  # BLOCK

    def test_already_completed_step_blocked(self, engine_instance, tmp_path):
        """已 COMPLETED 的步骤再次 enter 应被 BLOCK。"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)
        engine_instance.enter("P0")  # auto-complete

        rc = engine_instance.enter("P0")
        assert rc == 1  # BLOCK：已完成
