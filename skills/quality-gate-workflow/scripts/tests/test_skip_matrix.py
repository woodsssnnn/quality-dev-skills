"""test_skip_matrix.py — Skip 矩阵（lite / no-e2e / 内容驱动）测试"""

import json
import os
from pathlib import Path

import pytest

from tests.conftest import COMPLETED, NOT_STARTED, SKIPPED


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _make_dirs(tmp_path):
    for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)


# ── 静态 skip matrix（init 时确定）─────────────────────────────────────────

class TestStaticSkipMatrix:

    def test_lite_mode_skips_p15_p16_p17(self, engine_instance, tmp_path):
        """--lite 模式使 P1.5/P1.6/P1.7 被 skip"""
        engine_instance.init("gate1", "prd", ["--lite"])
        steps = engine_instance.state["steps"]
        for s in ["P1.5", "P1.6", "P1.7"]:
            assert steps[s]["status"] == SKIPPED, f"{s} 应为 SKIPPED"

    def test_no_e2e_skips_s45(self, engine_instance, tmp_path):
        """gate2 不带 --e2e 时 S4.5 被 skip"""
        engine_instance.init("gate2", "prd", [])
        steps = engine_instance.state["steps"]
        assert steps["S4.5"]["status"] == SKIPPED


# ── 内容驱动 skip（complete P1/P2/S3 时触发）───────────────────────────────

class TestContentDrivenSkip:

    def test_content_driven_skip_pure_frontend(self, engine_instance, tmp_path):
        """P1 complete 时 has_backend=False → P1.5 skip"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)
        engine_instance.enter("P0")
        engine_instance.complete("P0")
        engine_instance.enter("P1")
        engine_instance.complete("P1", meta={"has_backend": False})
        assert engine_instance.state["steps"]["P1.5"]["status"] == SKIPPED

    def test_content_driven_skip_greenfield(self, engine_instance, tmp_path):
        """P1 complete 时 is_greenfield=True → P1.6 skip"""
        engine_instance.init("gate1", "prd", [])
        _make_dirs(tmp_path)
        engine_instance.enter("P0")
        engine_instance.complete("P0")
        engine_instance.enter("P1")
        engine_instance.complete("P1", meta={"is_greenfield": True})
        assert engine_instance.state["steps"]["P1.6"]["status"] == SKIPPED

    def test_content_driven_skip_bug_clear(self, engine_instance, tmp_path):
        """P1 complete 时 mode=bug + bug_clarity=clear → P1.7 skip"""
        engine_instance.init("gate1", "bug", [])
        _make_dirs(tmp_path)
        engine_instance.enter("P0")
        engine_instance.complete("P0")
        engine_instance.enter("P1")
        engine_instance.complete("P1", meta={"bug_clarity": "clear"})
        assert engine_instance.state["steps"]["P1.7"]["status"] == SKIPPED

    def test_content_driven_skip_opt_no_prd(self, engine_instance, tmp_path):
        """P1 complete 时 mode=opt + no_prd_change=True → P1.7 skip"""
        engine_instance.init("gate1", "opt", [])
        _make_dirs(tmp_path)
        engine_instance.enter("P0")
        engine_instance.complete("P0")
        engine_instance.enter("P1")
        engine_instance.complete("P1", meta={"no_prd_change": True})
        assert engine_instance.state["steps"]["P1.7"]["status"] == SKIPPED

    def test_content_driven_skip_bug_fix_short(self, engine_instance, tmp_path):
        """P2 complete 时 mode=bug + fix_lines≤10 → P2.5 skip"""
        # 使用 lite 模式跳过 P1.5/P1.6/P1.7，以便顺利完成 P1-check
        engine_instance.init("gate1", "bug", ["--lite"])
        _make_dirs(tmp_path)
        engine_instance.enter("P0")
        engine_instance.complete("P0")
        engine_instance.enter("P1")
        engine_instance.complete("P1")
        engine_instance.enter("P1-check")
        engine_instance.complete("P1-check")
        engine_instance.enter("P2")
        engine_instance.complete("P2", meta={"fix_lines": 5})
        assert engine_instance.state["steps"]["P2.5"]["status"] == SKIPPED

    def test_content_driven_skip_no_sql(self, engine_instance, tmp_path):
        """S3 complete 时 has_sql=False → S3.5 skip"""
        engine_instance.init("gate2", "prd", [])
        _make_dirs(tmp_path)
        # 快速推进到 S3
        steps = engine_instance.state["steps"]
        for s in ["S0", "S1", "S2", "S2.5"]:
            steps[s]["status"] = COMPLETED
        engine_instance.enter("S3")
        engine_instance.complete("S3", meta={"has_sql": False})
        assert engine_instance.state["steps"]["S3.5"]["status"] == SKIPPED
