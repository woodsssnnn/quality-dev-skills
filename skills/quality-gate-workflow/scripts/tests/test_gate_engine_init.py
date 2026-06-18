"""test_gate_engine_init.py — GateEngine.init() 正/负路径测试"""

import json
import os
from pathlib import Path

import pytest


class TestInitGates:
    """各 gate 类型的初始化测试"""

    def test_init_gate1_success(self, engine_instance):
        rc = engine_instance.init("gate1", "prd", [])
        assert rc == 0
        assert engine_instance.state is not None
        assert engine_instance.state["gate"] == "gate1"

    def test_init_gate2_success(self, engine_instance):
        rc = engine_instance.init("gate2", "prd", [])
        assert rc == 0
        assert engine_instance.state["gate"] == "gate2"

    def test_init_debug_success(self, engine_instance):
        rc = engine_instance.init("debug", "debug", [])
        assert rc == 0
        assert engine_instance.state["gate"] == "debug"

    def test_init_audit_success(self, engine_instance):
        rc = engine_instance.init("audit", "audit", [])
        assert rc == 0
        assert engine_instance.state["gate"] == "audit"

    def test_init_invalid_gate(self, engine_instance):
        rc = engine_instance.init("gate99", "prd", [])
        assert rc == 1  # output_block 返回 1


class TestInitSession:
    """会话状态相关测试"""

    def test_init_duplicate_session_blocked(self, initialized_gate1_engine, tmp_path):
        """已初始化的会话（IN_PROGRESS）再次 init 应被阻止"""
        # 必须先 enter 一个步骤使状态变为 IN_PROGRESS
        for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
            (tmp_path / d).mkdir(parents=True, exist_ok=True)
        initialized_gate1_engine.enter("P0")
        assert initialized_gate1_engine.state["status"] == "IN_PROGRESS"
        rc = initialized_gate1_engine.init("gate1", "prd", [])
        assert rc == 1

    def test_init_session_id_generated(self, engine_instance):
        engine_instance.init("gate1", "prd", [])
        sid = engine_instance.state["session_id"]
        assert sid.startswith("ses_")

    def test_init_steps_initialized(self, engine_instance):
        engine_instance.init("gate1", "prd", [])
        steps = engine_instance.state["steps"]
        from tests.conftest import GATE1_STEPS, NOT_STARTED
        for s in GATE1_STEPS:
            assert s in steps
            assert steps[s]["status"] in (NOT_STARTED, "SKIPPED")

    def test_init_state_file_created(self, engine_instance, tmp_engine_state):
        engine_instance.init("gate1", "prd", [])
        assert os.path.exists(tmp_engine_state)

    def test_init_state_json_valid(self, engine_instance, tmp_engine_state):
        engine_instance.init("gate1", "prd", [])
        with open(tmp_engine_state, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert "session_id" in data
        assert "steps" in data


class TestInitSkipMatrix:
    """skip matrix 初始化测试"""

    def test_init_skip_matrix_lite(self, engine_instance):
        engine_instance.init("gate1", "prd", ["--lite"])
        skip = engine_instance.state["skip_matrix"]
        assert "P1.5" in skip
        assert "P1.6" in skip
        assert "P1.7" in skip
        # 对应步骤状态应为 SKIPPED
        from tests.conftest import SKIPPED
        assert engine_instance.state["steps"]["P1.5"]["status"] == SKIPPED

    def test_init_skip_matrix_no_e2e(self, engine_instance):
        """gate2 不带 --e2e 时 S4.5 应被 skip"""
        engine_instance.init("gate2", "prd", [])
        skip = engine_instance.state["skip_matrix"]
        assert "S4.5" in skip
        from tests.conftest import SKIPPED
        assert engine_instance.state["steps"]["S4.5"]["status"] == SKIPPED
