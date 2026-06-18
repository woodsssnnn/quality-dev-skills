"""test_prd_changed.py — GateEngine.prd_changed() 正/负路径测试"""

import json
import os
from pathlib import Path

import pytest

from tests.conftest import COMPLETED, NOT_STARTED, RUNNING, SKIPPED


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _make_dirs(tmp_path):
    for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)


def _setup_active_gate2(engine, tmp_path):
    """初始化 gate2 并推进到 IN_PROGRESS（S1 RUNNING）"""
    engine.init("gate2", "prd", [])
    _make_dirs(tmp_path)
    engine.enter("S0")
    engine.complete("S0")
    engine.enter("S1")
    engine.complete("S1")
    engine.enter("S2")


# ── prd_changed 测试 ────────────────────────────────────────────────────────

class TestPrdChanged:

    def test_prd_changed_cosmetic(self, engine_instance, tmp_path):
        """cosmetic 级别不重置任何步骤"""
        _setup_active_gate2(engine_instance, tmp_path)
        rc = engine_instance.prd_changed("cosmetic")
        assert rc == 0
        # S2 仍为 RUNNING（未被重置）
        assert engine_instance.state["steps"]["S2"]["status"] == RUNNING

    def test_prd_changed_minor_resets_s4(self, engine_instance, tmp_path):
        """minor 级别重置 S4（若 S4 已 COMPLETED）"""
        engine_instance.init("gate2", "prd", [])
        _make_dirs(tmp_path)
        # 手动将 S4 设为 COMPLETED
        steps = engine_instance.state["steps"]
        for s in ["S0", "S1", "S2", "S2.5", "S3", "S3.5", "S4"]:
            steps[s]["status"] = COMPLETED
        engine_instance.enter("S5")  # 使状态为 IN_PROGRESS（需要 S4 COMPLETED）
        # 先让 S5 回到 NOT_STARTED，S4 重新 enter 再 complete 比较复杂
        # 简化：直接把状态改回来
        steps["S5"]["status"] = NOT_STARTED
        steps["S4"]["status"] = COMPLETED
        engine_instance.state["status"] = "IN_PROGRESS"

        rc = engine_instance.prd_changed("minor")
        assert rc == 0
        assert engine_instance.state["steps"]["S4"]["status"] == NOT_STARTED

    def test_prd_changed_major_resets_all(self, engine_instance, tmp_path):
        """major 级别重置 Gate 2 大部分步骤"""
        engine_instance.init("gate2", "prd", [])
        _make_dirs(tmp_path)
        steps = engine_instance.state["steps"]
        for s in ["S0", "S1", "S2", "S2.5", "S3", "S3.5", "S4"]:
            steps[s]["status"] = COMPLETED
        engine_instance.state["status"] = "IN_PROGRESS"

        rc = engine_instance.prd_changed("major")
        assert rc == 0
        # S1~S4 从 COMPLETED 被重置为 NOT_STARTED
        for s in ["S1", "S2", "S2.5", "S3", "S3.5", "S4"]:
            assert engine_instance.state["steps"][s]["status"] == NOT_STARTED
        # S4.5 初始即为 SKIPPED，不在 COMPLETED/RUNNING 集合中，不会被重置
        assert engine_instance.state["steps"]["S4.5"]["status"] == SKIPPED
        # S5 初始为 NOT_STARTED，也不会被重置
        assert engine_instance.state["steps"]["S5"]["status"] == NOT_STARTED

    def test_prd_changed_no_active_session(self, engine_instance, tmp_path):
        """无活跃 Gate 2 会话时，建议走 RV1-RV5"""
        engine_instance.init("gate1", "prd", [])
        rc = engine_instance.prd_changed("minor")
        assert rc == 0  # 仍返回 OK，附带建议

    def test_prd_changed_invalid_impact(self, engine_instance, tmp_path):
        """无效的影响级别应被阻止"""
        engine_instance.init("gate2", "prd", [])
        rc = engine_instance.prd_changed("catastrophic")
        assert rc == 1
