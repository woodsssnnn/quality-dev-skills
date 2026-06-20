"""
test_report_generator.py — report-generator.py 的 TDD 测试套件。

覆盖：步骤→报告映射、数据采集器、6 种模板渲染器、集成入口、CLI。
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

# ── 加载 report-generator.py（文件名含连字符，需用 importlib）──────────────
_REPORT_GEN_PATH = Path(__file__).parent.parent / "report-generator.py"

spec = importlib.util.spec_from_file_location("report_generator", _REPORT_GEN_PATH)
report_generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report_generator)

sys.modules["report_generator"] = report_generator

# 导出
REPORT_STEP_MAP = report_generator.REPORT_STEP_MAP
gather_verification_data = report_generator.gather_verification_data
gather_step_flow = report_generator.gather_step_flow
render_plan_completeness = report_generator.render_plan_completeness
render_gate1_verifier = report_generator.render_gate1_verifier
render_gate2_audit = report_generator.render_gate2_audit
render_debug_fix = report_generator.render_debug_fix
render_session_summary = report_generator.render_session_summary
render_prd_impact = report_generator.render_prd_impact
generate_report = report_generator.generate_report
maybe_generate_report = report_generator.maybe_generate_report


# ── 辅助函数 ─────────────────────────────────────────────────────────────────

def _make_state(tmp_path, gate="gate1", mode="prd", steps_data=None, **extra):
    """构建最小可用的引擎状态 dict。"""
    state = {
        "schema_version": "1.0",
        "session_id": "ses_test_001",
        "gate": gate,
        "mode": mode,
        "flags": [],
        "status": "IN_PROGRESS",
        "current_step": None,
        "steps": steps_data or {},
        "skip_matrix": {},
        "feedback_rounds": 0,
        "max_feedback_rounds": 2,
        "created_at": "2026-06-20T10:00:00",
    }
    state.update(extra)
    return state


def _make_step(status="COMPLETED", artifacts=None, meta=None, started_at=None, completed_at=None):
    return {
        "status": status,
        "started_at": started_at or "2026-06-20T10:00:00",
        "completed_at": completed_at or "2026-06-20T10:05:00",
        "artifacts": artifacts or [],
        "meta": meta or {},
    }


def _write_verification_json(tmp_path, data=None):
    """写入测试用的 unit-test.json。"""
    ver_dir = tmp_path / "docs" / "verification"
    ver_dir.mkdir(parents=True, exist_ok=True)
    if data is None:
        data = {
            "units": [
                {
                    "id": "U1",
                    "name": "test-unit",
                    "items": [
                        {
                            "id": "U1-01",
                            "description": "item PASS",
                            "status": "PASS",
                            "toolCallId": "Agent|S4|2026-06-20T10:00:00",
                            "codeRefs": ["src/main.py:10"],
                        },
                        {
                            "id": "U1-02",
                            "description": "item FAIL",
                            "status": "FAIL",
                            "toolCallId": "Agent|S4|2026-06-20T10:01:00",
                        },
                        {
                            "id": "U1-03",
                            "description": "item PENDING",
                            "status": "PENDING",
                        },
                    ],
                }
            ],
            "verifierReports": [
                {"agent": "verifier-1", "result": "PASS", "timestamp": "2026-06-20T10:00:00"},
            ],
        }
    jf = ver_dir / "unit-test.json"
    jf.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return ver_dir


# ===== TestReportStepMap =====

class TestReportStepMap:
    """步骤→报告类型映射测试。"""

    def test_gate1_steps_mapped(self):
        """P3 映射到 plan-completeness，P4 映射到 gate1-verifier。"""
        assert REPORT_STEP_MAP["P3"] == "plan-completeness"
        assert REPORT_STEP_MAP["P4"] == "gate1-verifier"

    def test_gate2_steps_mapped(self):
        """S4 映射到 audit，S5 映射到 session-summary。"""
        assert REPORT_STEP_MAP["S4"] == "audit"
        assert REPORT_STEP_MAP["S5"] == "session-summary"

    def test_debug_and_special_mapped(self):
        """D3 映射到 debug-fix，P5 映射到 session-summary。"""
        assert REPORT_STEP_MAP["D3"] == "debug-fix"
        assert REPORT_STEP_MAP["P5"] == "session-summary"


# ===== TestGatherVerificationData =====

class TestGatherVerificationData:
    """数据采集器测试。"""

    def test_gather_normal(self, tmp_path):
        """正常 JSON 数据采集。"""
        ver_dir = _write_verification_json(tmp_path)
        data = gather_verification_data(str(ver_dir))
        assert data["total_items"] == 3
        assert data["pass_count"] == 1
        assert data["fail_count"] == 1
        assert data["pending_count"] == 1
        assert len(data["verifier_reports"]) == 1

    def test_gather_empty_dir(self, tmp_path):
        """空目录返回零统计。"""
        ver_dir = tmp_path / "docs" / "verification"
        ver_dir.mkdir(parents=True, exist_ok=True)
        data = gather_verification_data(str(ver_dir))
        assert data["total_items"] == 0
        assert data["pass_count"] == 0

    def test_gather_no_dir(self, tmp_path):
        """目录不存在时返回空统计。"""
        data = gather_verification_data(str(tmp_path / "nonexistent"))
        assert data["total_items"] == 0

    def test_gather_corrupt_json(self, tmp_path):
        """损坏 JSON 文件被跳过。"""
        ver_dir = tmp_path / "docs" / "verification"
        ver_dir.mkdir(parents=True, exist_ok=True)
        (ver_dir / "unit-bad.json").write_text("{broken json", encoding="utf-8")
        data = gather_verification_data(str(ver_dir))
        assert data["total_items"] == 0

    def test_gather_multiple_files(self, tmp_path):
        """多个 unit-*.json 文件聚合统计。"""
        ver_dir = tmp_path / "docs" / "verification"
        ver_dir.mkdir(parents=True, exist_ok=True)
        for i in range(3):
            d = {"units": [{"id": f"U{i}", "name": f"unit-{i}", "items": [
                {"id": f"U{i}-01", "description": "item", "status": "PASS",
                 "toolCallId": "Agent|S4|2026-06-20T10:00:00", "codeRefs": ["f.py:1"]},
            ]}], "verifierReports": []}
            (ver_dir / f"unit-{i}.json").write_text(json.dumps(d), encoding="utf-8")
        data = gather_verification_data(str(ver_dir))
        assert data["total_items"] == 3
        assert data["pass_count"] == 3


# ===== TestGatherStepFlow =====

class TestGatherStepFlow:
    """步骤流数据采集测试。"""

    def test_all_completed(self):
        """全部完成的步骤流。"""
        steps = {"P0": _make_step(), "P1": _make_step(), "P2": _make_step()}
        state = _make_state(None, steps_data=steps)
        flow = gather_step_flow(state)
        assert len(flow) == 3
        assert all(f["status"] == "✅" for f in flow)

    def test_partial_completed(self):
        """部分完成的步骤流。"""
        steps = {
            "P0": _make_step("COMPLETED"),
            "P1": _make_step("RUNNING"),
            "P2": _make_step("NOT_STARTED"),
        }
        state = _make_state(None, steps_data=steps)
        flow = gather_step_flow(state)
        assert len(flow) == 3
        assert flow[0]["status"] == "✅"
        assert flow[1]["status"] == "🔄"
        assert flow[2]["status"] == "⏳"

    def test_with_skipped(self):
        """含 SKIP 的步骤流。"""
        steps = {
            "P0": _make_step("COMPLETED"),
            "P1.5": _make_step("SKIPPED", meta={"skip_reason": "lite-mode"}),
        }
        state = _make_state(None, steps_data=steps)
        flow = gather_step_flow(state)
        assert flow[1]["status"] == "⏭ SKIP"


# ===== TestRenderGate1Completeness =====

class TestRenderGate1Completeness:
    """Plan Completeness Report 渲染测试。"""

    def test_render_has_header(self, tmp_path):
        """渲染结果包含报告标题。"""
        state = _make_state(tmp_path)
        ver_data = {"total_items": 5, "pass_count": 3, "fail_count": 1,
                    "pending_count": 1, "verifier_reports": [], "units": []}
        result = render_plan_completeness(state, ver_data)
        assert "Plan Completeness Report" in result

    def test_render_statistics(self, tmp_path):
        """统计数字正确渲染。"""
        state = _make_state(tmp_path)
        ver_data = {"total_items": 10, "pass_count": 6, "fail_count": 2,
                    "pending_count": 2, "verifier_reports": [], "units": []}
        result = render_plan_completeness(state, ver_data)
        assert "COVERED: 6" in result or "6" in result
        assert "MISSING: 2" in result or "FAIL: 2" in result

    def test_render_date(self, tmp_path):
        """日期字段被填充（非占位符）。"""
        state = _make_state(tmp_path)
        ver_data = {"total_items": 0, "pass_count": 0, "fail_count": 0,
                    "pending_count": 0, "verifier_reports": [], "units": []}
        result = render_plan_completeness(state, ver_data)
        assert "2026" in result

    def test_render_session_id(self, tmp_path):
        """session_id 被填充。"""
        state = _make_state(tmp_path)
        ver_data = {"total_items": 0, "pass_count": 0, "fail_count": 0,
                    "pending_count": 0, "verifier_reports": [], "units": []}
        result = render_plan_completeness(state, ver_data)
        assert "ses_test_001" in result


# ===== TestRenderGate1Verifier =====

class TestRenderGate1Verifier:
    """Gate 1 Verifier Report 渲染测试。"""

    def test_render_has_header(self, tmp_path):
        state = _make_state(tmp_path)
        ver_data = {"total_items": 3, "pass_count": 2, "fail_count": 1,
                    "pending_count": 0, "verifier_reports": [
                        {"agent": "v1", "result": "PASS", "timestamp": "2026-06-20T10:00:00"}
                    ], "units": []}
        result = render_gate1_verifier(state, ver_data)
        assert "Gate 1 Verifier Report" in result

    def test_render_verifier_reports(self, tmp_path):
        state = _make_state(tmp_path)
        ver_data = {"total_items": 2, "pass_count": 1, "fail_count": 1,
                    "pending_count": 0, "verifier_reports": [
                        {"agent": "v1", "result": "PASS", "timestamp": "2026-06-20T10:00:00"},
                        {"agent": "v2", "result": "FAIL", "timestamp": "2026-06-20T10:01:00"},
                    ], "units": []}
        result = render_gate1_verifier(state, ver_data)
        assert "v1" in result
        assert "v2" in result

    def test_render_empty_reports(self, tmp_path):
        state = _make_state(tmp_path)
        ver_data = {"total_items": 0, "pass_count": 0, "fail_count": 0,
                    "pending_count": 0, "verifier_reports": [], "units": []}
        result = render_gate1_verifier(state, ver_data)
        assert "Gate 1 Verifier Report" in result


# ===== TestRenderGate2Audit =====

class TestRenderGate2Audit:
    """Gate 2 Audit Report 渲染测试。"""

    def test_render_has_header(self, tmp_path):
        state = _make_state(tmp_path, gate="gate2")
        ver_data = {"total_items": 5, "pass_count": 4, "fail_count": 1,
                    "pending_count": 0, "verifier_reports": [], "units": [
                        {"id": "U1", "name": "unit-1", "items": [
                            {"id": "U1-01", "description": "test", "status": "PASS",
                             "toolCallId": "Agent|S4|2026-06-20T10:00:00", "codeRefs": ["f.py:1"]}
                        ]}
                    ]}
        result = render_gate2_audit(state, ver_data)
        assert "Audit Report" in result

    def test_render_unit_summary_table(self, tmp_path):
        """Unit 汇总表正确渲染。"""
        state = _make_state(tmp_path, gate="gate2")
        ver_data = {"total_items": 2, "pass_count": 1, "fail_count": 1,
                    "pending_count": 0, "verifier_reports": [], "units": [
                        {"id": "U1", "name": "unit-1", "items": [
                            {"id": "U1-01", "description": "pass", "status": "PASS",
                             "toolCallId": "Agent|S4|2026-06-20T10:00:00", "codeRefs": ["f.py:1"]}
                        ]},
                        {"id": "U2", "name": "unit-2", "items": [
                            {"id": "U2-01", "description": "fail", "status": "FAIL",
                             "toolCallId": "Agent|S4|2026-06-20T10:01:00"}
                        ]},
                    ]}
        result = render_gate2_audit(state, ver_data)
        assert "U1" in result
        assert "U2" in result

    def test_render_pass_fail_counts(self, tmp_path):
        state = _make_state(tmp_path, gate="gate2")
        ver_data = {"total_items": 10, "pass_count": 7, "fail_count": 3,
                    "pending_count": 0, "verifier_reports": [], "units": []}
        result = render_gate2_audit(state, ver_data)
        assert "7" in result
        assert "3" in result

    def test_render_feedback_rounds(self, tmp_path):
        """反馈轮次信息被包含。"""
        state = _make_state(tmp_path, gate="gate2", feedback_rounds=1, max_feedback_rounds=2)
        ver_data = {"total_items": 0, "pass_count": 0, "fail_count": 0,
                    "pending_count": 0, "verifier_reports": [], "units": []}
        result = render_gate2_audit(state, ver_data)
        assert "1/2" in result


# ===== TestRenderDebugFix =====

class TestRenderDebugFix:
    """Debug Fix Verification Report 渲染测试。"""

    def test_render_has_header(self, tmp_path):
        state = _make_state(tmp_path, gate="debug", mode="bug")
        result = render_debug_fix(state, {})
        assert "Fix Verification" in result

    def test_render_fix_criteria(self, tmp_path):
        """修复标准区域被渲染。"""
        steps = {
            "D1": _make_step("COMPLETED", meta={"fix_criteria": "消除 NPE"}),
            "D2": _make_step("COMPLETED"),
            "D3": _make_step("COMPLETED"),
        }
        state = _make_state(tmp_path, gate="debug", mode="bug", steps_data=steps)
        result = render_debug_fix(state, {})
        assert "Fix Verification" in result
        assert "ses_test_001" in result

    def test_render_overall_conclusion(self, tmp_path):
        state = _make_state(tmp_path, gate="debug", mode="bug")
        result = render_debug_fix(state, {})
        assert "PASS" in result or "FAIL" in result or "PLACEHOLDER" in result


# ===== TestRenderSessionSummary =====

class TestRenderSessionSummary:
    """Session Summary 渲染测试。"""

    def test_render_has_header(self, tmp_path):
        steps = {"P0": _make_step(), "P1": _make_step()}
        state = _make_state(tmp_path, steps_data=steps)
        result = render_session_summary(state, {})
        assert "QGW Session" in result

    def test_render_execution_flow(self, tmp_path):
        """Execution Flow 表被渲染。"""
        steps = {
            "P0": _make_step("COMPLETED"),
            "P1": _make_step("COMPLETED"),
            "P1.5": _make_step("SKIPPED", meta={"skip_reason": "lite"}),
        }
        state = _make_state(tmp_path, steps_data=steps)
        result = render_session_summary(state, {})
        assert "Execution Flow" in result or "Step" in result
        assert "P0" in result

    def test_render_session_id(self, tmp_path):
        steps = {"P0": _make_step()}
        state = _make_state(tmp_path, steps_data=steps)
        result = render_session_summary(state, {})
        assert "ses_test_001" in result

    def test_render_trigger_info(self, tmp_path):
        """触发参数信息被渲染。"""
        state = _make_state(tmp_path, gate="gate1", mode="prd")
        state["flags"] = ["--strict"]
        result = render_session_summary(state, {})
        assert "gate1" in result or "prd" in result


# ===== TestRenderPrdImpact =====

class TestRenderPrdImpact:
    """PRD Revision Impact Report 渲染测试。"""

    def test_render_has_header(self, tmp_path):
        state = _make_state(tmp_path, gate="gate2")
        prd_data = {"impact": "minor", "scope": "§2.3", "reset_steps": ["S4"]}
        result = render_prd_impact(state, prd_data)
        assert "PRD Revision Impact" in result

    def test_render_impact_level(self, tmp_path):
        state = _make_state(tmp_path, gate="gate2")
        prd_data = {"impact": "major", "scope": "§1.0", "reset_steps": ["S1", "S2", "S3", "S4"]}
        result = render_prd_impact(state, prd_data)
        assert "major" in result

    def test_render_reset_steps(self, tmp_path):
        state = _make_state(tmp_path, gate="gate2")
        prd_data = {"impact": "minor", "scope": "§2.3", "reset_steps": ["S4"]}
        result = render_prd_impact(state, prd_data)
        assert "S4" in result


# ===== TestMaybeGenerateReport =====

class TestMaybeGenerateReport:
    """集成入口 maybe_generate_report 测试。"""

    def test_matching_step_generates_report(self, tmp_path, monkeypatch):
        """匹配的步骤生成报告文件。"""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "docs" / "reports").mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "sessions").mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "verification").mkdir(parents=True, exist_ok=True)

        steps = {"P0": _make_step(), "P1": _make_step(), "P2": _make_step(), "P3": _make_step()}
        state = _make_state(tmp_path, steps_data=steps)
        result = maybe_generate_report("P3", state)
        assert result is not None
        assert os.path.exists(result)

    def test_non_matching_step_returns_none(self, tmp_path, monkeypatch):
        """非映射步骤返回 None。"""
        monkeypatch.chdir(tmp_path)
        state = _make_state(tmp_path)
        result = maybe_generate_report("P0", state)
        assert result is None

    def test_report_written_to_reports_dir(self, tmp_path, monkeypatch):
        """报告写入 docs/reports/ 目录。"""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "docs" / "reports").mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "sessions").mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "verification").mkdir(parents=True, exist_ok=True)

        steps = {"S0": _make_step(), "S4": _make_step()}
        state = _make_state(tmp_path, gate="gate2", steps_data=steps)
        result = maybe_generate_report("S4", state)
        assert result is not None
        assert "docs" in result or "reports" in result


# ===== TestGenerateReport =====

class TestGenerateReport:
    """generate_report 按类型生成测试。"""

    def test_generate_session_summary(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "docs" / "sessions").mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "reports").mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "verification").mkdir(parents=True, exist_ok=True)

        steps = {"P0": _make_step(), "P1": _make_step()}
        state = _make_state(tmp_path, steps_data=steps)
        result = generate_report("session-summary", state)
        assert result is not None
        content = Path(result).read_text(encoding="utf-8")
        assert "QGW Session" in content

    def test_generate_invalid_type_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        state = _make_state(tmp_path)
        result = generate_report("nonexistent-type", state)
        assert result is None

    def test_generate_plan_completeness(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "docs" / "reports").mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "verification").mkdir(parents=True, exist_ok=True)

        state = _make_state(tmp_path)
        result = generate_report("plan-completeness", state)
        assert result is not None
        content = Path(result).read_text(encoding="utf-8")
        assert "Plan Completeness Report" in content
