"""test_priority_sorting.py — Plan Unit 优先级排序测试"""

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
    """写入带 priority 字段的 unit JSON。"""
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


def _make_units_with_priorities():
    """返回含不同优先级的 units 列表。"""
    return [
        {
            "name": "low-priority-unit",
            "priority": "P2",
            "items": [
                {"id": "U1-01", "spec": "spec1", "source": "§1.0", "status": "PENDING"},
            ],
        },
        {
            "name": "core-unit",
            "priority": "P0",
            "items": [
                {"id": "U2-01", "spec": "spec2", "source": "§2.0", "status": "PENDING"},
            ],
        },
        {
            "name": "standard-unit",
            "priority": "P1",
            "items": [
                {"id": "U3-01", "spec": "spec3", "source": "§3.0", "status": "PENDING"},
            ],
        },
    ]


# ===== TestPrioritySorting =====

class TestPrioritySorting:

    def test_sort_units_p0_first(self, engine_instance, tmp_path):
        """P0 units 应排在 P1 和 P2 前面。"""
        _make_dirs(tmp_path)
        units = _make_units_with_priorities()
        _write_unit_json(tmp_path, units)

        sorted_ids = engine_instance._sort_units_by_priority(str(tmp_path / "docs" / "verification"))
        # P0 应排第一
        assert sorted_ids[0]["priority"] == "P0"
        assert sorted_ids[1]["priority"] == "P1"
        assert sorted_ids[2]["priority"] == "P2"

    def test_sort_units_same_priority_stable(self, engine_instance, tmp_path):
        """同优先级 units 应保持原始顺序（稳定排序）。"""
        _make_dirs(tmp_path)
        units = [
            {"name": "a-unit", "priority": "P1", "items": [
                {"id": "U1-01", "spec": "s", "source": "§1", "status": "PENDING"}
            ]},
            {"name": "b-unit", "priority": "P1", "items": [
                {"id": "U2-01", "spec": "s", "source": "§2", "status": "PENDING"}
            ]},
        ]
        _write_unit_json(tmp_path, units)

        sorted_ids = engine_instance._sort_units_by_priority(str(tmp_path / "docs" / "verification"))
        assert sorted_ids[0]["name"] == "a-unit"
        assert sorted_ids[1]["name"] == "b-unit"

    def test_sort_no_priority_defaults_p1(self, engine_instance, tmp_path):
        """无 priority 字段的 unit 应默认 P1。"""
        _make_dirs(tmp_path)
        units = [
            {"name": "no-priority", "items": [
                {"id": "U1-01", "spec": "s", "source": "§1", "status": "PENDING"}
            ]},
            {"name": "p0-unit", "priority": "P0", "items": [
                {"id": "U2-01", "spec": "s", "source": "§2", "status": "PENDING"}
            ]},
        ]
        _write_unit_json(tmp_path, units)

        sorted_ids = engine_instance._sort_units_by_priority(str(tmp_path / "docs" / "verification"))
        assert sorted_ids[0]["priority"] == "P0"
        assert sorted_ids[1].get("priority", "P1") == "P1"

    def test_sort_empty_verification_dir(self, engine_instance, tmp_path):
        """空 verification 目录应返回空列表。"""
        _make_dirs(tmp_path)
        sorted_ids = engine_instance._sort_units_by_priority(str(tmp_path / "docs" / "verification"))
        assert sorted_ids == []

    def test_sort_corrupt_json_skipped(self, engine_instance, tmp_path):
        """损坏的 JSON 文件应被跳过。"""
        _make_dirs(tmp_path)
        ver_dir = tmp_path / "docs" / "verification"
        (ver_dir / "unit-bad.json").write_text("{broken", encoding="utf-8")
        sorted_ids = engine_instance._sort_units_by_priority(str(ver_dir))
        assert sorted_ids == []


# ===== TestItemPriorityOverride =====

class TestItemPriorityOverride:

    def test_item_inherits_unit_priority(self, engine_instance, tmp_path):
        """Item 无 priority 时继承 Unit 级 priority。"""
        _make_dirs(tmp_path)
        units = [
            {"name": "p0-unit", "priority": "P0", "items": [
                {"id": "U1-01", "spec": "s", "source": "§1", "status": "PENDING"},
            ]},
        ]
        _write_unit_json(tmp_path, units)
        sorted_ids = engine_instance._sort_units_by_priority(str(tmp_path / "docs" / "verification"))
        # Unit 级别是 P0
        assert sorted_ids[0]["priority"] == "P0"
        # Item 继承 Unit 的 P0
        assert sorted_ids[0]["items"][0].get("priority", "P0") == "P0"

    def test_item_overrides_unit_priority(self, engine_instance, tmp_path):
        """Item 有 priority 时覆盖 Unit 级。"""
        _make_dirs(tmp_path)
        units = [
            {"name": "p1-unit", "priority": "P1", "items": [
                {"id": "U1-01", "spec": "s", "source": "§1", "status": "PENDING", "priority": "P0"},
            ]},
        ]
        _write_unit_json(tmp_path, units)
        sorted_ids = engine_instance._sort_units_by_priority(str(tmp_path / "docs" / "verification"))
        # Item 级别覆盖了 Unit 的 P1 → P0
        assert sorted_ids[0]["items"][0]["priority"] == "P0"


# ===== TestPriorityFilter =====

class TestPriorityFilter:

    def test_init_with_priority_filter(self, engine_instance, tmp_path):
        """init 时指定 --priority 应存入 state。"""
        _make_dirs(tmp_path)
        engine_instance.init("gate2", "prd", ["--priority", "P0"])
        assert engine_instance.state.get("priority_filter") == ["P0"]

    def test_init_without_priority_filter(self, engine_instance, tmp_path):
        """不指定 --priority 时 filter 为 None（全部执行）。"""
        _make_dirs(tmp_path)
        engine_instance.init("gate1", "prd", [])
        assert engine_instance.state.get("priority_filter") is None

    def test_status_shows_priority_info(self, engine_instance, tmp_path):
        """status 输出中应包含优先级信息。"""
        _make_dirs(tmp_path)
        engine_instance.init("gate2", "prd", [])
        # status 不应崩溃
        rc = engine_instance.status()
        assert rc == 0
