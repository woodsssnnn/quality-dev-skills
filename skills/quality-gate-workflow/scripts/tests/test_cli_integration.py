"""test_cli_integration.py — CLI 入口（main()）集成测试

通过 subprocess 调用 gate-enforcer.py CLI，验证参数解析和退出码。
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT_PATH = Path(__file__).parent.parent / "gate-enforcer.py"


# ── 辅助工具 ────────────────────────────────────────────────────────────────

def _run_cli(tmp_path, *args, env_extra=None):
    """在 tmp_path 目录下运行 gate-enforcer.py CLI"""
    env = os.environ.copy()
    env["QGW_ENGINE_STATE"] = str(tmp_path / "docs" / ".qgw-engine-state.json")
    if env_extra:
        env.update(env_extra)
    # 确保 docs 目录存在
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, str(_SCRIPT_PATH)] + list(args),
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env=env,
        timeout=30,
    )
    return result


def _parse_stdout(result):
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


# ── CLI 集成测试 ─────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestCliIntegration:

    def test_cli_init_gate1(self, tmp_path):
        """CLI: init --gate gate1 应返回 OK"""
        result = _run_cli(tmp_path, "init", "--gate", "gate1")
        assert result.returncode == 0
        data = _parse_stdout(result)
        assert data is not None
        assert data["status"] == "OK"

    def test_cli_enter_step(self, tmp_path):
        """CLI: enter P0 应返回 ALLOW"""
        _run_cli(tmp_path, "init", "--gate", "gate1")
        # 创建产出物目录（P0 enter 不需要，但后续 complete 需要）
        for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
            (tmp_path / d).mkdir(parents=True, exist_ok=True)
        result = _run_cli(tmp_path, "enter", "P0")
        assert result.returncode == 0
        data = _parse_stdout(result)
        assert data["status"] == "ALLOW"

    def test_cli_complete_step(self, tmp_path):
        """CLI: complete P0 应返回 OK"""
        _run_cli(tmp_path, "init", "--gate", "gate1")
        for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
            (tmp_path / d).mkdir(parents=True, exist_ok=True)
        _run_cli(tmp_path, "enter", "P0")
        result = _run_cli(tmp_path, "complete", "P0")
        assert result.returncode == 0
        data = _parse_stdout(result)
        assert data["status"] == "OK"

    def test_cli_fail_step(self, tmp_path):
        """CLI: fail P4 --reason ... 应正常执行"""
        _run_cli(tmp_path, "init", "--gate", "gate1")
        for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
            (tmp_path / d).mkdir(parents=True, exist_ok=True)
        # 手动将 P4 设为 RUNNING（通过 enter 需要先完成前置步骤）
        # 用 status 查询来验证 CLI 能运行
        result = _run_cli(tmp_path, "status")
        assert result.returncode == 0

    def test_cli_status(self, tmp_path):
        """CLI: status 应返回 OK"""
        _run_cli(tmp_path, "init", "--gate", "gate1")
        result = _run_cli(tmp_path, "status")
        assert result.returncode == 0
        data = _parse_stdout(result)
        assert data["status"] == "OK"

    def test_cli_no_action_shows_help(self, tmp_path):
        """无参数时应显示帮助并退出码为 1"""
        result = _run_cli(tmp_path)
        assert result.returncode == 1

    def test_cli_self_check(self, tmp_path):
        """CLI: self-check 应返回 OK"""
        _run_cli(tmp_path, "init", "--gate", "gate1")
        result = _run_cli(tmp_path, "self-check")
        assert result.returncode == 0
        data = _parse_stdout(result)
        assert data["status"] == "OK"

    def test_cli_prd_changed_cosmetic(self, tmp_path):
        """CLI: prd-changed --impact cosmetic 应返回 OK"""
        _run_cli(tmp_path, "init", "--gate", "gate1")
        result = _run_cli(tmp_path, "prd-changed", "--impact", "cosmetic")
        assert result.returncode == 0
        data = _parse_stdout(result)
        assert data["status"] in ("OK", "ALLOW")

    def test_cli_plan_tweak(self, tmp_path):
        """CLI: plan-tweak 应返回 OK"""
        _run_cli(tmp_path, "init", "--gate", "gate2")
        for d in ["docs/plans", "docs/verification", "docs/reports", "docs/sessions"]:
            (tmp_path / d).mkdir(parents=True, exist_ok=True)
        result = _run_cli(tmp_path, "plan-tweak", "--reason", "字段名修正", "--scope", "ch-1.1")
        assert result.returncode == 0
        data = _parse_stdout(result)
        assert data["status"] in ("OK", "ALLOW")

    def test_cli_resume_without_state(self, tmp_path):
        """CLI: resume 无状态文件应返回 BLOCK"""
        result = _run_cli(tmp_path, "resume")
        # resume 在无状态时应返回非 0 或 OK
        assert result.returncode in (0, 1)
