"""test_gate_engine_complete.py — GateEngine.complete() 正/负路径测试"""

import json
import os
from pathlib import Path

import pytest

from tests.conftest import COMPLETED, NOT_STARTED, RUNNING, SKIPPED


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _make_dirs(tmp_path):
    for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)


def _setup_p0(engine, tmp_path):
    """进入 P0"""
    _make_dirs(tmp_path)
    engine.enter("P0")


# ── 基本 complete 测试 ────────────────────────────────────────────────────────

class TestCompleteBasic:

    def test_complete_p0_success(self, initialized_gate1_engine, tmp_path):
        """P0 complete 需通过 dirs_exist 检查"""
        _setup_p0(initialized_gate1_engine, tmp_path)
        rc = initialized_gate1_engine.complete("P0")
        assert rc == 0
        assert initialized_gate1_engine.state["steps"]["P0"]["status"] == COMPLETED

    def test_complete_with_artifacts(self, initialized_gate1_engine, tmp_path):
        """传入真实存在的文件作为 artifacts"""
        _setup_p0(initialized_gate1_engine, tmp_path)
        artifact = tmp_path / "docs" / "plans" / "plan.md"
        artifact.write_text("# Plan", encoding="utf-8")
        rc = initialized_gate1_engine.complete(
            "P0", artifacts=[str(artifact.relative_to(tmp_path))]
        )
        assert rc == 0
        assert str(artifact.relative_to(tmp_path)) in initialized_gate1_engine.state["steps"]["P0"]["artifacts"]

    def test_complete_artifact_not_exist_blocked(self, initialized_gate1_engine, tmp_path):
        """artifacts 中的路径不存在时应被阻止"""
        _setup_p0(initialized_gate1_engine, tmp_path)
        rc = initialized_gate1_engine.complete("P0", artifacts=["docs/nonexistent.md"])
        assert rc == 1

    def test_complete_not_running_blocked(self, initialized_gate1_engine, tmp_path):
        """步骤未 enter（非 RUNNING）时 complete 被阻止"""
        rc = initialized_gate1_engine.complete("P0")
        assert rc == 1  # P0 是 NOT_STARTED，非 RUNNING

    def test_complete_writes_checkpoint(self, initialized_gate1_engine, tmp_path):
        """complete 后应在 CHECKPOINT_DIR 写入 checkpoint 文件"""
        _setup_p0(initialized_gate1_engine, tmp_path)
        initialized_gate1_engine.complete("P0")
        cp_path = tmp_path / "docs" / ".qgw-checkpoints" / "P0.json"
        assert cp_path.exists()

    def test_complete_updates_gate_state(self, initialized_gate1_engine, tmp_path):
        """complete 后 .gate-state 文件应被更新"""
        _setup_p0(initialized_gate1_engine, tmp_path)
        initialized_gate1_engine.complete("P0")
        gs_path = tmp_path / "docs" / ".gate-state"
        assert gs_path.exists()

    def test_complete_next_step_calculated(self, initialized_gate1_engine, tmp_path):
        """complete 后应计算 next_step"""
        _setup_p0(initialized_gate1_engine, tmp_path)
        # P0 完成，需要捕获 stdout 来检查 next_step（或检查 state）
        rc = initialized_gate1_engine.complete("P0")
        assert rc == 0
        # 完成后 current_step 应为 None
        assert initialized_gate1_engine.state["current_step"] is None

    def test_complete_session_complete(self, engine_instance, tmp_path):
        """当所有步骤完成后，会话状态应为 COMPLETED"""
        engine_instance.init("debug", "debug", [])
        # 完成所有 Debug 步骤
        for step in ["D1", "D2", "D3"]:
            engine_instance.enter(step)
            engine_instance.complete(step)
        # D4 需要 toolCallId
        engine_instance.enter("D4")
        engine_instance.complete("D4", tool_call_id="Agent|D4|2026-01-01T00:00:00")
        assert engine_instance.state["status"] == "COMPLETED"


# ── toolCallId 相关测试 ───────────────────────────────────────────────────────

class TestCompleteToolCallId:

    def test_complete_toolcallid_required_p4(self, engine_instance, tmp_path):
        """P4 需要 toolCallId，缺失时应被阻止"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)
        # 快速推进到 P4（需要完成 P0~P3）
        # 简化：直接手动设置状态
        steps = engine_instance.state["steps"]
        for s in ["P0", "P1", "P1.5", "P1.6", "P1.7", "P1-check", "P2", "P2.5", "P3"]:
            steps[s]["status"] = COMPLETED
        engine_instance.enter("P4")
        rc = engine_instance.complete("P4")
        assert rc == 1  # 缺 toolCallId

    def test_complete_toolcallid_required_s4(self, engine_instance, tmp_path):
        """S4 需要 toolCallId"""
        engine_instance.init("gate2", "prd", [])
        _make_dirs(tmp_path)
        steps = engine_instance.state["steps"]
        for s in ["S0", "S1", "S2", "S2.5", "S3", "S3.5"]:
            steps[s]["status"] = COMPLETED
        engine_instance.enter("S4")
        rc = engine_instance.complete("S4")
        assert rc == 1  # 缺 toolCallId

    def test_complete_toolcallid_format_invalid(self, engine_instance, tmp_path):
        """toolCallId 格式无效时应被阻止"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)
        steps = engine_instance.state["steps"]
        for s in ["P0", "P1", "P1.5", "P1.6", "P1.7", "P1-check", "P2", "P2.5", "P3"]:
            steps[s]["status"] = COMPLETED
        engine_instance.enter("P4")
        rc = engine_instance.complete("P4", tool_call_id="bad-format")
        assert rc == 1


# ── 内容驱动 skip 测试 ───────────────────────────────────────────────────────

class TestCompleteContentDrivenSkip:

    def test_complete_content_driven_skip_p1(self, engine_instance, tmp_path):
        """P1 complete 时传入 has_backend=False 应触发 P1.5 skip"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)
        engine_instance.enter("P0")
        engine_instance.complete("P0")
        engine_instance.enter("P1")
        engine_instance.complete("P1", meta={"has_backend": False})
        assert engine_instance.state["steps"]["P1.5"]["status"] == SKIPPED
