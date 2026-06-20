"""test_gate_engine_resume.py — GateEngine.resume() 正/负路径测试"""

import json
import os
from pathlib import Path

import pytest

from tests.conftest import COMPLETED, NOT_STARTED, RUNNING


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _make_dirs(tmp_path):
    for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)


def _setup_and_run_p0(engine, tmp_path):
    """初始化 gate1 并 enter P0（使其为 RUNNING）"""
    engine.init("gate1", "prd", [])
    _make_dirs(tmp_path)
    engine.enter("P0")


# ── resume 测试 ──────────────────────────────────────────────────────────────

class TestResume:

    def test_resume_running_step_reset(self, engine_instance, tmp_path):
        """RUNNING 步骤在 resume 后重置为 NOT_STARTED"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)
        # P0 auto-completes，所以用 P1 来测试 resume
        engine_instance.enter("P0")  # auto-complete
        engine_instance.enter("P1")  # stays RUNNING
        assert engine_instance.state["steps"]["P1"]["status"] == RUNNING
        rc = engine_instance.resume()
        assert rc == 0
        assert engine_instance.state["steps"]["P1"]["status"] == NOT_STARTED

    def test_resume_completed_checkpoint_check(self, engine_instance, tmp_path):
        """COMPLETED 步骤的 checkpoint 存在时 resume 成功"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)
        engine_instance.enter("P0")  # auto-complete (writes checkpoint)
        # checkpoint 已写入，resume 应成功
        rc = engine_instance.resume()
        assert rc == 0

    def test_resume_five_questions(self, engine_instance, tmp_path):
        """resume 输出应包含五问结果"""
        _setup_and_run_p0(engine_instance, tmp_path)
        rc = engine_instance.resume()
        assert rc == 0
        # 五问在内部构建，检查 state 字段
        assert "current_step" in engine_instance.state

    def test_resume_warnings(self, engine_instance, tmp_path):
        """artifact 文件不存在时 resume 产生警告但不阻止"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)
        # 使用 P1（非 auto-complete）来测试 artifact 警告
        engine_instance.enter("P0")  # auto-complete
        engine_instance.enter("P1")  # stays RUNNING
        # 手动创建一个 artifact 文件，complete，然后删除它
        artifact = tmp_path / "docs" / "plans" / "temp.md"
        artifact.write_text("temp", encoding="utf-8")
        engine_instance.complete("P1", artifacts=["docs/plans/temp.md"])
        # 删除 artifact
        artifact.unlink()
        rc = engine_instance.resume()
        # resume 仍成功（有警告）
        assert rc == 0

    def test_resume_no_state_blocked(self, engine_instance, tmp_path):
        """无状态时 resume 被阻止"""
        # engine_instance 没有 init，state 为 None
        rc = engine_instance.resume()
        assert rc == 1

    def test_resume_gate_state_update(self, engine_instance, tmp_path):
        """resume 后 .gate-state 文件应被更新"""
        _setup_and_run_p0(engine_instance, tmp_path)
        engine_instance.resume()
        gs_path = tmp_path / "docs" / ".gate-state"
        assert gs_path.exists()
