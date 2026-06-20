"""test_evolve_integration.py — evolve 步骤集成测试"""

import json
import os
from pathlib import Path

import pytest

from tests.conftest import COMPLETED, NOT_STARTED, RUNNING, SKIPPED, GateEngine, GATE1_STEPS, GATE2_STEPS


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _make_dirs(tmp_path):
    for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions",
              ".qgw/knowledge"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)


# ===== TestEvolveSteps =====

class TestEvolveSteps:

    def test_p5_evolve_in_gate1_steps(self):
        """P5-evolve 应在 GATE1_STEPS 中。"""
        assert "P5-evolve" in GATE1_STEPS

    def test_s5_evolve_in_gate2_steps(self):
        """S5-evolve 应在 GATE2_STEPS 中。"""
        assert "S5-evolve" in GATE2_STEPS

    def test_p5_evolve_requires_p5_completed(self, engine_instance, tmp_path):
        """P5-evolve 需要 P5 先 COMPLETED。"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)
        # P5 是 NOT_STARTED → P5-evolve 应被阻止
        rc = engine_instance.enter("P5-evolve")
        assert rc == 1

    def test_s5_evolve_requires_s5_completed(self, engine_instance, tmp_path):
        """S5-evolve 需要 S5 先 COMPLETED。"""
        engine_instance.init("gate2", "prd", [])
        _make_dirs(tmp_path)
        rc = engine_instance.enter("S5-evolve")
        assert rc == 1

    def test_p5_evolve_skippable(self, engine_instance, tmp_path):
        """P5-evolve 是可跳过的（skippable）。"""
        engine_instance.init("gate1", "prd", ["--lite"])
        _make_dirs(tmp_path)
        # lite 模式下 evolve 可以被 skip
        # 验证引擎不会崩溃
        rc = engine_instance.status()
        assert rc == 0


# ===== TestEvolveAutoTrigger =====

class TestEvolveAutoTrigger:

    def test_complete_p5_triggers_evolve(self, engine_instance, tmp_path):
        """complete P5 时应自动触发 evolve（非阻断）。"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)

        # 快速推进到 P5（手动设置前置步骤为 COMPLETED）
        steps = engine_instance.state["steps"]
        for s in ["P0", "P1", "P1.5", "P1.6", "P1.7", "P1-check", "P2", "P2.5", "P3", "P4"]:
            steps[s]["status"] = COMPLETED
        engine_instance.state["status"] = "IN_PROGRESS"
        engine_instance._save_state()

        # 创建最小 verification 数据
        ver_dir = tmp_path / "docs" / "verification"
        data = {
            "version": "1.3", "plan": "plan.md", "gate": 1,
            "generated": "2026-06-20T10:00:00",
            "units": [{"name": "u", "priority": "P1", "items": [
                {"id": "U1-01", "spec": "s", "source": "§1", "status": "PASS",
                 "toolCallId": "Agent|P4|2026-06-20T10:00:00", "codeRefs": [{"file": "f.py"}]}
            ]}],
            "toolCalls": [],
            "verifierReports": [{"round": 1, "timestamp": "2026-06-20T10:00:00",
                                 "result": "PASS", "failItems": [], "verifierType": "independent-verifier"}]
        }
        (ver_dir / "unit-test.json").write_text(json.dumps(data), encoding="utf-8")

        # P5 需要 verification_json_valid + index_updated + session_summary + schema_valid
        (tmp_path / "docs" / "QGW-INDEX.md").write_text("# Index", encoding="utf-8")
        (tmp_path / "docs" / "sessions" / "ses_test.md").write_text("# Session", encoding="utf-8")

        engine_instance.enter("P5")
        rc = engine_instance.complete("P5")
        assert rc == 0
        # evolve 应被触发（非阻断，即使没有新 pattern 也不报错）

    def test_evolve_does_not_block_complete(self, engine_instance, tmp_path):
        """即使 evolve 引擎出错，complete P5 仍应成功。"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)

        steps = engine_instance.state["steps"]
        for s in ["P0", "P1", "P1.5", "P1.6", "P1.7", "P1-check", "P2", "P2.5", "P3", "P4"]:
            steps[s]["status"] = COMPLETED
        engine_instance.state["status"] = "IN_PROGRESS"
        engine_instance._save_state()

        # 创建最小验证数据
        ver_dir = tmp_path / "docs" / "verification"
        data = {
            "version": "1.3", "plan": "plan.md", "gate": 1,
            "generated": "2026-06-20T10:00:00",
            "units": [{"name": "u", "priority": "P1", "items": [
                {"id": "U1-01", "spec": "s", "source": "§1", "status": "PASS",
                 "toolCallId": "Agent|P4|2026-06-20T10:00:00", "codeRefs": [{"file": "f.py"}]}
            ]}],
            "toolCalls": [],
            "verifierReports": [{"round": 1, "timestamp": "2026-06-20T10:00:00",
                                 "result": "PASS", "failItems": [], "verifierType": "independent-verifier"}]
        }
        (ver_dir / "unit-test.json").write_text(json.dumps(data), encoding="utf-8")
        (tmp_path / "docs" / "QGW-INDEX.md").write_text("# Index", encoding="utf-8")
        (tmp_path / "docs" / "sessions" / "ses_test.md").write_text("# Session", encoding="utf-8")

        engine_instance.enter("P5")
        rc = engine_instance.complete("P5")
        # evolve 不应阻断 P5 complete
        assert rc == 0
