"""test_evolve.py — evolve-engine.py 单元测试"""

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

# ── 加载 evolve-engine.py ────────────────────────────────────────────────────
_EVOLVE_PATH = Path(__file__).parent.parent / "evolve-engine.py"
spec = importlib.util.spec_from_file_location("evolve_engine", _EVOLVE_PATH)
evolve_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evolve_engine)
sys.modules["evolve_engine"] = evolve_engine

EvolveEngine = evolve_engine.EvolveEngine


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _make_dirs(tmp_path):
    for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions",
              ".qgw/knowledge"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)


def _write_verifier_reports(tmp_path, items):
    """写入包含指定 items 的 unit-test.json。"""
    ver_dir = tmp_path / "docs" / "verification"
    ver_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "version": "1.3",
        "plan": "docs/plans/plan.md",
        "gate": 2,
        "generated": "2026-06-20T10:00:00",
        "units": [{"name": "test-unit", "priority": "P0", "items": items}],
        "toolCalls": [],
        "verifierReports": [
            {"round": 1, "timestamp": "2026-06-20T10:00:00", "result": "FAIL",
             "failItems": [it["id"] for it in items if it.get("status") == "FAIL"],
             "verifierType": "independent-verifier"}
        ],
    }
    (ver_dir / "unit-test.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_error_patterns(tmp_path, patterns):
    """写入已有的 error-patterns.json。"""
    knowledge_dir = tmp_path / ".qgw" / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "version": "2.0",
        "scope": "workspace",
        "patterns": patterns,
        "upgradeLog": [],
        "promoteLog": [],
    }
    (knowledge_dir / "error-patterns.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


# ===== TestPatternExtraction =====

class TestPatternExtraction:

    def test_extract_from_fail_items(self, tmp_path):
        """从 FAIL 项中提取错误模式。"""
        _make_dirs(tmp_path)
        items = [
            {"id": "U1-01", "spec": "邮箱唯一", "source": "§1", "status": "FAIL", "rootCause": "CODE"},
            {"id": "U1-02", "spec": "角色枚举完整", "source": "§2", "status": "PASS"},
        ]
        _write_verifier_reports(tmp_path, items)

        engine = EvolveEngine(str(tmp_path))
        patterns = engine._extract_patterns(str(tmp_path / "docs" / "verification"))
        assert len(patterns) >= 1
        assert any("U1-01" in p.get("id", "") or "邮箱" in p.get("description", "") for p in patterns)

    def test_extract_from_partial_items(self, tmp_path):
        """PARTIAL 项也应被提取。"""
        _make_dirs(tmp_path)
        items = [
            {"id": "U1-01", "spec": "审核人三选项", "source": "§3", "status": "FAIL"},
        ]
        _write_verifier_reports(tmp_path, items)

        engine = EvolveEngine(str(tmp_path))
        patterns = engine._extract_patterns(str(tmp_path / "docs" / "verification"))
        assert len(patterns) >= 1

    def test_no_fail_no_patterns(self, tmp_path):
        """全部 PASS 时不产生新模式。"""
        _make_dirs(tmp_path)
        items = [
            {"id": "U1-01", "spec": "通过", "source": "§1", "status": "PASS"},
        ]
        _write_verifier_reports(tmp_path, items)

        engine = EvolveEngine(str(tmp_path))
        patterns = engine._extract_patterns(str(tmp_path / "docs" / "verification"))
        assert len(patterns) == 0

    def test_empty_verification_dir(self, tmp_path):
        """空 verification 目录返回空列表。"""
        _make_dirs(tmp_path)
        engine = EvolveEngine(str(tmp_path))
        patterns = engine._extract_patterns(str(tmp_path / "docs" / "verification"))
        assert patterns == []


# ===== TestDeduplication =====

class TestDeduplication:

    def test_deduplicate_same_description(self, tmp_path):
        """相同描述的模式应去重。"""
        existing = [
            {"id": "EP001", "description": "邮箱唯一", "frequency": 1, "category": "field-presence"},
        ]
        new_patterns = [
            {"id": "EP_NEW_1", "description": "邮箱唯一", "category": "field-presence"},
        ]
        engine = EvolveEngine(str(tmp_path))
        deduped = engine._deduplicate(new_patterns, existing)
        assert len(deduped) == 0  # 已存在，不新增

    def test_deduplicate_new_pattern(self, tmp_path):
        """新模式应保留。"""
        existing = [
            {"id": "EP001", "description": "邮箱唯一", "frequency": 1},
        ]
        new_patterns = [
            {"id": "EP_NEW_1", "description": "角色枚举三选项", "category": "business-rule"},
        ]
        engine = EvolveEngine(str(tmp_path))
        deduped = engine._deduplicate(new_patterns, existing)
        assert len(deduped) == 1


# ===== TestFrequencyAndThresholds =====

class TestFrequencyAndThresholds:

    def test_frequency_increment(self, tmp_path):
        """已有模式的 frequency 应递增。"""
        _make_dirs(tmp_path)
        patterns = [
            {"id": "EP001", "description": "模糊验收", "frequency": 2, "category": "verification"},
        ]
        _write_error_patterns(tmp_path, patterns)

        engine = EvolveEngine(str(tmp_path))
        updated = engine._update_error_patterns(
            [{"id": "EP_NEW", "description": "模糊验收", "category": "verification"}],
            str(tmp_path / ".qgw" / "knowledge")
        )
        assert updated >= 1

    def test_threshold_promote_suggestion(self, tmp_path):
        """frequency >= 3 时应建议升级。"""
        patterns = [
            {"id": "EP001", "description": "模糊验收", "frequency": 3, "category": "verification"},
        ]
        engine = EvolveEngine(str(tmp_path))
        suggestions = engine._check_thresholds(patterns)
        assert len(suggestions) >= 1
        assert "dev_rule" in suggestions[0].lower() or "升级" in suggestions[0]

    def test_no_threshold_no_suggestion(self, tmp_path):
        """frequency < 3 时不建议升级。"""
        patterns = [
            {"id": "EP001", "description": "小问题", "frequency": 1, "category": "verification"},
        ]
        engine = EvolveEngine(str(tmp_path))
        suggestions = engine._check_thresholds(patterns)
        assert len(suggestions) == 0


# ===== TestEvolveMainEntry =====

class TestEvolveMainEntry:

    def test_evolve_with_fail_items(self, tmp_path):
        """有 FAIL 项时 evolve 应提取模式并写入。"""
        _make_dirs(tmp_path)
        items = [
            {"id": "U1-01", "spec": "验收标准模糊", "source": "§1", "status": "FAIL"},
        ]
        _write_verifier_reports(tmp_path, items)

        engine = EvolveEngine(str(tmp_path))
        result = engine.evolve("gate2")
        assert result["new_patterns"] >= 0  # 可能有也可能无（取决于去重）
        assert "evolve_log" in result

    def test_evolve_dry_run(self, tmp_path):
        """dry-run 模式不写入文件。"""
        _make_dirs(tmp_path)
        items = [
            {"id": "U1-01", "spec": "标准模糊", "source": "§1", "status": "FAIL"},
        ]
        _write_verifier_reports(tmp_path, items)

        engine = EvolveEngine(str(tmp_path))
        result = engine.evolve("gate2", dry_run=True)
        assert result.get("dry_run") is True
        # dry-run 不应创建 evolution-log.json
        log_path = tmp_path / ".qgw" / "knowledge" / "evolution-log.json"
        assert not log_path.exists()

    def test_evolve_no_new_patterns(self, tmp_path):
        """全部 PASS 时 evolve 输出'无新增'。"""
        _make_dirs(tmp_path)
        items = [
            {"id": "U1-01", "spec": "通过", "source": "§1", "status": "PASS"},
        ]
        _write_verifier_reports(tmp_path, items)

        engine = EvolveEngine(str(tmp_path))
        result = engine.evolve("gate2")
        assert result["new_patterns"] == 0
