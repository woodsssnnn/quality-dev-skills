"""test_bug_blocking.py — P0 Bug 阻塞低优先级步骤测试"""

import json
import os
from pathlib import Path

import pytest

from tests.conftest import COMPLETED, NOT_STARTED, RUNNING, SKIPPED, GateEngine


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _make_dirs(tmp_path):
    for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)


def _write_unit_json(tmp_path, units_data):
    """写入带 priority + status 的 unit JSON。"""
    ver_dir = tmp_path / "docs" / "verification"
    ver_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "version": "1.3",
        "plan": "docs/plans/plan.md",
        "gate": 1,
        "generated": "2026-06-20T10:00:00",
        "units": units_data,
        "toolCalls": [],
    }
    jf = ver_dir / "unit-test.json"
    jf.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return jf


def _setup_gate2_with_units(engine, tmp_path, units):
    """初始化 gate2 并写入 unit JSON。"""
    engine.init("gate2", "prd", [])
    _make_dirs(tmp_path)
    _write_unit_json(tmp_path, units)
    # 手动将 S0 设为 COMPLETED
    engine.state["steps"]["S0"]["status"] = COMPLETED
    engine.state["status"] = "IN_PROGRESS"
    engine._save_state()


# ===== TestBugBlocking =====

class TestBugBlocking:

    def test_p0_fail_blocks_p1_enter(self, engine_instance, tmp_path):
        """P0 item FAIL 时应阻塞 P1 优先级相关步骤。"""
        units = [
            {"name": "core", "priority": "P0", "items": [
                {"id": "U1-01", "spec": "s", "source": "§1", "status": "FAIL",
                 "toolCallId": "Agent|S4|2026-06-20T10:00:00"},
            ]},
            {"name": "standard", "priority": "P1", "items": [
                {"id": "U2-01", "spec": "s", "source": "§2", "status": "PENDING"},
            ]},
        ]
        _setup_gate2_with_units(engine_instance, tmp_path, units)

        # 检查 bug 阻塞
        blocked, reason = engine_instance._check_bug_block("S1", str(tmp_path / "docs" / "verification"))
        assert blocked is True
        assert "P0" in reason
        assert "U1-01" in reason

    def test_p0_pass_does_not_block(self, engine_instance, tmp_path):
        """P0 item PASS 时不应阻塞 P1。"""
        units = [
            {"name": "core", "priority": "P0", "items": [
                {"id": "U1-01", "spec": "s", "source": "§1", "status": "PASS",
                 "toolCallId": "Agent|S4|2026-06-20T10:00:00", "codeRefs": [{"file": "f.py"}]},
            ]},
            {"name": "standard", "priority": "P1", "items": [
                {"id": "U2-01", "spec": "s", "source": "§2", "status": "PENDING"},
            ]},
        ]
        _setup_gate2_with_units(engine_instance, tmp_path, units)

        blocked, reason = engine_instance._check_bug_block("S1", str(tmp_path / "docs" / "verification"))
        assert blocked is False

    def test_p1_fail_does_not_block_p2(self, engine_instance, tmp_path):
        """P1 FAIL 不应阻塞 P2。"""
        units = [
            {"name": "standard", "priority": "P1", "items": [
                {"id": "U1-01", "spec": "s", "source": "§1", "status": "FAIL"},
            ]},
            {"name": "low", "priority": "P2", "items": [
                {"id": "U2-01", "spec": "s", "source": "§2", "status": "PENDING"},
            ]},
        ]
        _setup_gate2_with_units(engine_instance, tmp_path, units)

        blocked, reason = engine_instance._check_bug_block("S1", str(tmp_path / "docs" / "verification"))
        assert blocked is False

    def test_no_verification_data_no_block(self, engine_instance, tmp_path):
        """无 verification 数据时不应阻塞。"""
        _make_dirs(tmp_path)
        engine_instance.init("gate2", "prd", [])

        blocked, reason = engine_instance._check_bug_block("S1", str(tmp_path / "docs" / "verification"))
        assert blocked is False

    def test_bug_block_resolved_after_fix(self, engine_instance, tmp_path):
        """P0 FAIL 修复后阻塞应解除。"""
        units = [
            {"name": "core", "priority": "P0", "items": [
                {"id": "U1-01", "spec": "s", "source": "§1", "status": "FAIL"},
            ]},
        ]
        _setup_gate2_with_units(engine_instance, tmp_path, units)

        # 先检查是阻塞的
        blocked, _ = engine_instance._check_bug_block("S1", str(tmp_path / "docs" / "verification"))
        assert blocked is True

        # 修复：将 status 改为 PASS
        units[0]["items"][0]["status"] = "PASS"
        _write_unit_json(tmp_path, units)

        # 修复后不应阻塞
        blocked, _ = engine_instance._check_bug_block("S1", str(tmp_path / "docs" / "verification"))
        assert blocked is False

    def test_bug_block_corrupt_json_no_block(self, engine_instance, tmp_path):
        """损坏的 JSON 不应导致阻塞。"""
        _make_dirs(tmp_path)
        engine_instance.init("gate2", "prd", [])
        ver_dir = tmp_path / "docs" / "verification"
        (ver_dir / "unit-bad.json").write_text("{broken", encoding="utf-8")

        blocked, _ = engine_instance._check_bug_block("S1", str(ver_dir))
        assert blocked is False

    def test_mixed_priorities_only_p0_blocks(self, engine_instance, tmp_path):
        """P0+P1 混合时，只有 P0 FAIL 阻塞。"""
        units = [
            {"name": "core", "priority": "P0", "items": [
                {"id": "U1-01", "spec": "s", "source": "§1", "status": "PASS"},
            ]},
            {"name": "standard", "priority": "P1", "items": [
                {"id": "U2-01", "spec": "s", "source": "§2", "status": "FAIL"},
            ]},
            {"name": "low", "priority": "P2", "items": [
                {"id": "U3-01", "spec": "s", "source": "§3", "status": "PENDING"},
            ]},
        ]
        _setup_gate2_with_units(engine_instance, tmp_path, units)

        # P0 PASS，P1 FAIL → 不阻塞
        blocked, _ = engine_instance._check_bug_block("S1", str(tmp_path / "docs" / "verification"))
        assert blocked is False

    def test_s0_step_never_blocked(self, engine_instance, tmp_path):
        """S0 初始化步骤不应被 bug 阻塞。"""
        units = [
            {"name": "core", "priority": "P0", "items": [
                {"id": "U1-01", "spec": "s", "source": "§1", "status": "FAIL"},
            ]},
        ]
        _setup_gate2_with_units(engine_instance, tmp_path, units)

        blocked, _ = engine_instance._check_bug_block("S0", str(tmp_path / "docs" / "verification"))
        assert blocked is False

    def test_s5_step_never_blocked(self, engine_instance, tmp_path):
        """S5 提交步骤不应被 bug 阻塞。"""
        units = [
            {"name": "core", "priority": "P0", "items": [
                {"id": "U1-01", "spec": "s", "source": "§1", "status": "FAIL"},
            ]},
        ]
        _setup_gate2_with_units(engine_instance, tmp_path, units)

        blocked, _ = engine_instance._check_bug_block("S5", str(tmp_path / "docs" / "verification"))
        assert blocked is False
