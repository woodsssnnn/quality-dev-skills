"""
conftest.py — pytest fixtures for gate-enforcer.py tests.

所有 fixture 使用 tmp_path 隔离文件系统，确保测试间互不干扰。
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

# ── 加载 gate-enforcer.py（文件名含连字符，需用 importlib）──────────────
_GATE_ENFORCER_PATH = Path(__file__).parent.parent / "gate-enforcer.py"

spec = importlib.util.spec_from_file_location("gate_enforcer", _GATE_ENFORCER_PATH)
gate_enforcer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate_enforcer)

# 将模块注入 sys.modules 以便后续 import
sys.modules["gate_enforcer"] = gate_enforcer

# 从模块中导出常用符号
GateEngine = gate_enforcer.GateEngine
GATE1_STEPS = gate_enforcer.GATE1_STEPS
GATE2_STEPS = gate_enforcer.GATE2_STEPS
DEBUG_STEPS = gate_enforcer.DEBUG_STEPS
AUDIT_STEPS = gate_enforcer.AUDIT_STEPS
AUTO_COMPLETE_STEPS = gate_enforcer.AUTO_COMPLETE_STEPS
NOT_STARTED = gate_enforcer.NOT_STARTED
RUNNING = gate_enforcer.RUNNING
COMPLETED = gate_enforcer.COMPLETED
FAILED = gate_enforcer.FAILED
SKIPPED = gate_enforcer.SKIPPED


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_engine_state(tmp_path):
    """在临时目录创建状态文件路径，返回路径字符串。

    不预先创建文件，让 GateEngine.init() 自行写入。
    """
    state_dir = tmp_path / "docs"
    state_dir.mkdir(parents=True, exist_ok=True)
    return str(state_dir / ".qgw-engine-state.json")


@pytest.fixture
def mock_artifact_dirs(tmp_path, monkeypatch):
    """在工作临时目录中创建产出物所需的目录结构。"""
    monkeypatch.chdir(tmp_path)
    dirs = [
        tmp_path / "docs" / "plans",
        tmp_path / "docs" / "verification",
        tmp_path / "docs" / "reports",
        tmp_path / "docs" / "sessions",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture
def sample_verification_json(tmp_path, monkeypatch):
    """写入合规的 unit-test.json 测试数据到 docs/verification/。"""
    monkeypatch.chdir(tmp_path)
    ver_dir = tmp_path / "docs" / "verification"
    ver_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "units": [
            {
                "id": "U1",
                "name": "test-unit",
                "items": [
                    {
                        "id": "U1-01",
                        "description": "sample item PASS",
                        "status": "PASS",
                        "toolCallId": "Agent|S4|2026-01-01T00:00:00",
                        "codeRefs": ["src/main.py:10"],
                    },
                    {
                        "id": "U1-02",
                        "description": "sample item SKIPPED",
                        "status": "SKIPPED",
                    },
                ],
            }
        ],
        "verifierReports": [
            {
                "agent": "verifier-1",
                "result": "PASS",
                "timestamp": "2026-01-01T00:00:00",
            }
        ],
    }
    jf = ver_dir / "unit-test.json"
    jf.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return jf


@pytest.fixture
def engine_instance(tmp_path, tmp_engine_state, monkeypatch):
    """返回已绑定临时状态文件的 GateEngine 实例。

    同时 monkeypatch.chdir 到 tmp_path，使相对路径检查（如 docs/）
    在测试目录中进行。
    """
    monkeypatch.chdir(tmp_path)
    # 确保 docs 目录存在（状态文件写入时需要）
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    engine = GateEngine(state_file=tmp_engine_state)
    return engine


@pytest.fixture
def initialized_gate1_engine(engine_instance, tmp_path):
    """已运行 init --gate gate1 的引擎（在 tmp_path 下工作）。"""
    engine_instance.init("gate1", "prd", [])
    return engine_instance


@pytest.fixture
def initialized_gate2_engine(engine_instance, tmp_path):
    """已运行 init --gate gate2 的引擎（在 tmp_path 下工作）。"""
    engine_instance.init("gate2", "prd", [])
    return engine_instance
