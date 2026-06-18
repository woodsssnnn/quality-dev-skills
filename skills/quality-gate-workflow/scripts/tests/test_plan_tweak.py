"""test_plan_tweak.py — GateEngine.plan_tweak() 正/负路径测试"""

import json
import os
from pathlib import Path

import pytest

from tests.conftest import COMPLETED, NOT_STARTED, RUNNING


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _make_dirs(tmp_path):
    for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)


# ── plan_tweak 测试 ──────────────────────────────────────────────────────────

class TestPlanTweak:

    def test_plan_tweak_success(self, engine_instance, tmp_path):
        """Gate 2 中（S1-S3 期间）可执行 plan_tweak"""
        engine_instance.init("gate2", "prd", [])
        _make_dirs(tmp_path)
        engine_instance.enter("S0")
        engine_instance.complete("S0")
        engine_instance.enter("S1")
        # current_step = S1，在允许范围内
        rc = engine_instance.plan_tweak("需求微调", scope="ch-2.1")
        assert rc == 0
        assert "plan_tweaks" in engine_instance.state
        assert len(engine_instance.state["plan_tweaks"]) == 1

    def test_plan_tweak_not_gate2_blocked(self, engine_instance, tmp_path):
        """非 Gate 2 时 plan_tweak 被阻止"""
        engine_instance.init("gate1", "prd", [])
        rc = engine_instance.plan_tweak("微调原因")
        assert rc == 1

    def test_plan_tweak_after_s4_blocked(self, engine_instance, tmp_path):
        """S4 完成后 plan_tweak 被阻止"""
        engine_instance.init("gate2", "prd", [])
        _make_dirs(tmp_path)
        steps = engine_instance.state["steps"]
        for s in ["S0", "S1", "S2", "S2.5", "S3", "S3.5", "S4"]:
            steps[s]["status"] = COMPLETED
        # 设置 current_step 为 S5（在 S4 之后）
        engine_instance.state["status"] = "IN_PROGRESS"
        engine_instance.state["current_step"] = "S5"
        steps["S5"]["status"] = RUNNING

        rc = engine_instance.plan_tweak("微调原因")
        assert rc == 1

    def test_plan_tweak_record_count(self, engine_instance, tmp_path):
        """多次 plan_tweak 应累加记录"""
        engine_instance.init("gate2", "prd", [])
        _make_dirs(tmp_path)
        engine_instance.enter("S0")
        engine_instance.complete("S0")
        engine_instance.enter("S1")
        engine_instance.plan_tweak("第一次微调", scope="ch-1.1")
        engine_instance.plan_tweak("第二次微调", scope="ch-2.1")
        assert len(engine_instance.state["plan_tweaks"]) == 2
        assert engine_instance.state["plan_tweaks"][0]["reason"] == "第一次微调"
        assert engine_instance.state["plan_tweaks"][1]["scope"] == "ch-2.1"
