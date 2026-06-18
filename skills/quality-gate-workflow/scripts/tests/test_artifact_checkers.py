"""test_artifact_checkers.py — 产出物检查器正/负路径测试"""

import json
import os
from pathlib import Path

import pytest

import sys
import importlib.util

# 直接导入 gate_enforcer 模块（已在 conftest 中注册）
from tests.conftest import gate_enforcer


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _make_dirs(tmp_path):
    for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)


def _write_unit_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ── dirs_exist ───────────────────────────────────────────────────────────────

class TestDirsExist:

    def test_dirs_exist_pass(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_dirs(tmp_path)
        ok, msg = gate_enforcer.check_dirs_exist({})
        assert ok is True

    def test_dirs_exist_fail(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # 不创建任何目录
        ok, msg = gate_enforcer.check_dirs_exist({})
        assert ok is False
        assert "目录缺失" in msg


# ── plan_files_exist ─────────────────────────────────────────────────────────

class TestPlanFilesExist:

    def test_plan_files_exist_pass(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        plans_dir = tmp_path / "docs" / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)
        (plans_dir / "plan-01.md").write_text("# Plan", encoding="utf-8")
        ok, msg = gate_enforcer.check_plan_files_exist({})
        assert ok is True

    def test_plan_files_exist_fail(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        plans_dir = tmp_path / "docs" / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)
        # 不写入任何 .md 文件
        ok, msg = gate_enforcer.check_plan_files_exist({})
        assert ok is False


# ── verification_json_valid ──────────────────────────────────────────────────

class TestVerificationJsonValid:

    def test_verification_json_valid_pass(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ver_dir = tmp_path / "docs" / "verification"
        _write_unit_json(ver_dir / "unit-test.json", {"units": []})
        ok, msg = gate_enforcer.check_verification_json_valid({})
        assert ok is True

    def test_verification_json_valid_fail_no_files(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ver_dir = tmp_path / "docs" / "verification"
        ver_dir.mkdir(parents=True, exist_ok=True)
        ok, msg = gate_enforcer.check_verification_json_valid({})
        assert ok is False

    def test_verification_json_valid_fail_bad_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ver_dir = tmp_path / "docs" / "verification"
        ver_dir.mkdir(parents=True, exist_ok=True)
        (ver_dir / "unit-bad.json").write_text("not json", encoding="utf-8")
        ok, msg = gate_enforcer.check_verification_json_valid({})
        assert ok is False


# ── index_updated ─────────────────────────────────────────────────────────────

class TestIndexUpdated:

    def test_index_updated_pass(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "docs").mkdir(exist_ok=True)
        (tmp_path / "docs" / "QGW-INDEX.md").write_text("# Index", encoding="utf-8")
        ok, msg = gate_enforcer.check_index_updated({})
        assert ok is True

    def test_index_updated_fail(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ok, msg = gate_enforcer.check_index_updated({})
        assert ok is False


# ── toolcallid_complete ───────────────────────────────────────────────────────

class TestToolcallidComplete:

    def test_toolcallid_complete_pass(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ver_dir = tmp_path / "docs" / "verification"
        data = {
            "units": [{
                "id": "U1",
                "items": [{"id": "1", "status": "PASS", "toolCallId": "Agent|S4|2026-01-01T00:00:00"}]
            }]
        }
        _write_unit_json(ver_dir / "unit-test.json", data)
        ok, msg = gate_enforcer.check_toolcallid_complete({})
        assert ok is True

    def test_toolcallid_complete_fail(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ver_dir = tmp_path / "docs" / "verification"
        data = {
            "units": [{
                "id": "U1",
                "items": [{"id": "1", "status": "PASS"}]  # 缺 toolCallId
            }]
        }
        _write_unit_json(ver_dir / "unit-test.json", data)
        ok, msg = gate_enforcer.check_toolcallid_complete({})
        assert ok is False


# ── verifier_report_written ───────────────────────────────────────────────────

class TestVerifierReportWritten:

    def test_verifier_report_written_pass(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ver_dir = tmp_path / "docs" / "verification"
        data = {"verifierReports": [{"agent": "v1", "result": "PASS"}]}
        _write_unit_json(ver_dir / "unit-test.json", data)
        ok, msg = gate_enforcer.check_verifier_report_written({})
        assert ok is True

    def test_verifier_report_written_fail(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ver_dir = tmp_path / "docs" / "verification"
        data = {"verifierReports": []}
        _write_unit_json(ver_dir / "unit-test.json", data)
        ok, msg = gate_enforcer.check_verifier_report_written({})
        assert ok is False


# ── feedback_rounds ───────────────────────────────────────────────────────────

class TestFeedbackRounds:

    def test_feedback_rounds_pass(self):
        state = {"feedback_rounds": 1, "max_feedback_rounds": 2}
        ok, msg = gate_enforcer.check_feedback_rounds(state)
        assert ok is True

    def test_feedback_rounds_fail(self):
        state = {"feedback_rounds": 2, "max_feedback_rounds": 2}
        ok, msg = gate_enforcer.check_feedback_rounds(state)
        assert ok is False


# ── schema_valid ─────────────────────────────────────────────────────────────

class TestSchemaValid:

    def test_schema_valid_fallback(self, tmp_path, monkeypatch):
        """jsonschema 不可用时降级为基本检查（通过 mock 模拟 ImportError）"""
        monkeypatch.chdir(tmp_path)
        ver_dir = tmp_path / "docs" / "verification"
        data = {"units": []}  # 有 units 字段，基本检查通过
        _write_unit_json(ver_dir / "unit-test.json", data)
        # 强制让 jsonschema 不可用，测试降级路径
        import builtins
        real_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == "jsonschema":
                raise ImportError("mocked")
            return real_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", mock_import)
        ok, msg = gate_enforcer.check_schema_valid({})
        assert ok is True
        assert "jsonschema 不可用" in msg or "基本 Schema" in msg

    def test_schema_valid_basic_missing_units(self, tmp_path, monkeypatch):
        """降级模式下缺少 units 字段应失败"""
        monkeypatch.chdir(tmp_path)
        ver_dir = tmp_path / "docs" / "verification"
        data = {"name": "no-units"}
        _write_unit_json(ver_dir / "unit-test.json", data)
        # 强制让 jsonschema 不可用，测试降级路径
        import builtins
        real_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == "jsonschema":
                raise ImportError("mocked")
            return real_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", mock_import)
        ok, msg = gate_enforcer.check_schema_valid({})
        assert ok is False
        assert "units" in msg
