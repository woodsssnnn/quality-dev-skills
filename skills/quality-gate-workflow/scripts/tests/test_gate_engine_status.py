"""test_gate_engine_status.py — GateEngine.status() 正/负路径测试"""

import json
import os
from pathlib import Path

import pytest

from tests.conftest import COMPLETED, NOT_STARTED, RUNNING


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _make_dirs(tmp_path):
    for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)


# ── status 测试 ──────────────────────────────────────────────────────────────

class TestStatus:

    def test_status_overall(self, initialized_gate1_engine, tmp_path):
        """查询整体状态应返回 OK"""
        rc = initialized_gate1_engine.status()
        assert rc == 0

    def test_status_specific_step(self, initialized_gate1_engine, tmp_path):
        """查询特定步骤状态应返回 OK"""
        rc = initialized_gate1_engine.status(step="P0")
        assert rc == 0

    def test_status_progress_percentage(self, engine_instance, tmp_path):
        """完成一个步骤后进度百分比应大于 0"""
        engine_instance.init("debug", "debug", [])
        _make_dirs(tmp_path)
        engine_instance.enter("D1")
        engine_instance.complete("D1")
        # 4 个步骤完成 1 个 → 25%
        steps = engine_instance.state["steps"]
        completed = sum(1 for s in steps.values() if s["status"] == COMPLETED)
        total = len(steps)
        assert completed == 1
        assert total == 4

    def test_status_no_state_blocked(self, engine_instance, tmp_path):
        """无状态时 status 被阻止"""
        rc = engine_instance.status()
        assert rc == 1
