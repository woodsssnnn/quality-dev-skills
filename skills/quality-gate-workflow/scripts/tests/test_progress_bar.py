"""test_progress_bar.py — 进度可视化测试"""

import json
import os
from pathlib import Path

import pytest

from tests.conftest import COMPLETED, NOT_STARTED, RUNNING, SKIPPED, GateEngine


# ── 加载 progress-renderer.py ────────────────────────────────────────────────
import importlib.util
_RENDERER_PATH = Path(__file__).parent.parent / "progress-renderer.py"
spec = importlib.util.spec_from_file_location("progress_renderer", _RENDERER_PATH)
progress_renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(progress_renderer)

import sys
sys.modules["progress_renderer"] = progress_renderer

render_progress = progress_renderer.render_progress


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _make_dirs(tmp_path):
    for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)


def _make_step(status="COMPLETED", meta=None):
    return {
        "status": status,
        "started_at": "2026-06-20T10:00:00",
        "completed_at": "2026-06-20T10:05:00",
        "artifacts": [],
        "meta": meta or {},
    }


# ===== TestProgressBar =====

class TestProgressBar:

    def test_progress_bar_gate1(self, engine_instance, tmp_path):
        """Gate 1 进度条应包含步骤流和百分比。"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)

        result = render_progress(engine_instance.state)
        assert "Gate 1" in result
        assert "%" in result
        assert "P0" in result

    def test_progress_bar_zero_percent(self, engine_instance, tmp_path):
        """初始化后应显示 0% 进度。"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)

        result = render_progress(engine_instance.state)
        assert "0%" in result or "0.0%" in result

    def test_progress_bar_with_completed_steps(self, engine_instance, tmp_path):
        """部分步骤完成后应显示正确百分比。"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)

        # P0 auto-complete
        engine_instance.enter("P0")

        result = render_progress(engine_instance.state)
        assert "P0" in result
        # 进度应 > 0%
        assert "0%" not in result or "0.0%" not in result

    def test_progress_bar_with_skipped_steps(self, engine_instance, tmp_path):
        """含 SKIP 步骤的进度条应显示 ⏭ 符号。"""
        engine_instance.init("gate1", "prd", ["--lite"])
        _make_dirs(tmp_path)

        result = render_progress(engine_instance.state)
        # lite 模式下 P1.5/P1.6/P1.7 被 skip
        assert "⏭" in result or "SKIP" in result

    def test_progress_bar_gate2(self, engine_instance, tmp_path):
        """Gate 2 进度条应正常工作。"""
        engine_instance.init("gate2", "prd", [])
        _make_dirs(tmp_path)

        result = render_progress(engine_instance.state)
        assert "Gate 2" in result
        assert "S0" in result

    def test_progress_bar_shows_session_id(self, engine_instance, tmp_path):
        """进度条应显示 session_id。"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)

        result = render_progress(engine_instance.state)
        assert "ses_" in result
